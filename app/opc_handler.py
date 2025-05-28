from opcua import Client, ua
from flask import current_app
from typing import Optional
from app.database import crud
from app.database.models import db
from app.config import get_config_value

import requests
import threading
import queue


def int_to_bits(value, bits=16):
    return [(value >> i) & 1 for i in range(bits)]

def bits_from_value(value):
    if not isinstance(value, int):
        return []
    return int_to_bits(value, 32 if abs(value) > 32767 else 16)


class WebAlarmHandler:
    def __init__(self, app):
        self.app = app
        self.task_queue = queue.Queue()
        threading.Thread(target=self._worker_thread, daemon=True).start()

    def _worker_thread(self):
        while True:
            item_id = self.task_queue.get()
            try:
                with self.app.app_context():
                    print(f"🟡 Enviando POST para item {item_id}")
                    requests.post("http://localhost:5000/send", json={"item_id": item_id})
            except Exception as e:
                import traceback
                print(f"❌ Error al enviar POST para item {item_id}: {e}")
                traceback.print_exc()
            self.task_queue.task_done()

    def datachange_notification(self, node, val, data):
        node_id = node.nodeid.to_string()
        print(f"⚡ Cambio detectado en {node_id} => {val}")

        try:
            bits = bits_from_value(val)
            with self.app.app_context():
                for i, bit_val in enumerate(bits):
                    item = crud.get_item_by_order_and_node_id(db.session, i, node_id)
                    if item:
                        print(f"🟡 Actualizando nodo {node_id} item {item.id} con estado {bit_val}")
                        if item.estado == '0' and bit_val == 1:
                            self.task_queue.put(item.id)
                        item.estado = str(bit_val)
                        db.session.add(item)
                db.session.commit()
            # get handle and bits
            handle = data.monitored_item.ClientHandle
            print("Handle:", handle, "Bits:", bits)
        except Exception as e:
            print("❌ Error actualizando bits:", e)


class OpcUaClient:
    """
    Cliente OPC UA encapsulado: soporta conexión, lectura, escritura y suscripciones.
    """
    def __init__(self, endpoint: str, username: Optional[str] = None, password: Optional[str] = None):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.client = Client(endpoint)

        if self.username and self.password:
            self.client.set_user(self.username)
            self.client.set_password(self.password)

        self.subscription = None
        self.sub_handles = []
        self.is_connected = False

    # =======================
    # 🔌 CONEXIÓN
    # =======================

    def connect(self):
        """Establece conexión con el servidor OPC UA."""
        try:
            self.client.connect()
            self.is_connected = True
            print(f"✅ Conectado a {self.endpoint}")
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            self.is_connected = False

    def disconnect(self):
        """Cierra conexión y libera recursos."""
        try:
            if self.is_connected:
                self._cancel_all_subscriptions()
                self.client.disconnect()
                print("🔌 Cliente OPC desconectado correctamente")
        except Exception as e:
            print(f"❌ Error al desconectar: {e}")
        finally:
            self.is_connected = False

    # restore subscriptions:
    def restore_subscriptions(self):
        # verificar si esta conectado
        if not self.is_connected:
            print("❌ No esta conectado")
            return {"error": "No esta conectado", "status": "error"}

        # Verificar si hay suscripciones en el config.json
        suscripciones = get_config_value("TAGS_SUBSCRIBE")
        if not suscripciones:
            print("❌ No hay suscripciones en el config.json", suscripciones)
            return {"error": "No hay suscripciones en el config.json", "status": "error"}

        # Restaurar suscripciones
        handler = WebAlarmHandler(app=current_app._get_current_object())
        for suscripcion in suscripciones:
            self.subscribe(suscripcion, handler)

        # print subscripciones
        print("✅ Suscripciones restauradas")
        for handle in self.sub_handles:
            print(f"📡 Suscripción {handle} restaurada")
        
        return {"message": "Suscripciones restauradas", "status": "success", "handles": self.sub_handles}

    def change_endpoint(self, new_endpoint):
        self.endpoint = new_endpoint
        print(f"🔌 Cambiando endpoint a {self.endpoint}")
        print("Usuario:", self.username)
        print("Contraseña:", self.password)
        if self.is_connected:
            self.disconnect()

        self.client = Client(self.endpoint)

        if self.username and self.password:
            self.client.set_user(self.username)
            self.client.set_password(self.password)
        try:
            self.client.connect()
            self.is_connected = True
            print(f"✅ Conectado a {self.endpoint}")
        except Exception as e:
            print(f"❌ Error al conectar en cambio de enpoint: {e}")
            self.is_connected = False
    
    # change username and password
    def change_credentials(self, username, password):
        self.username = username
        self.password = password
        self.client.set_user(username)
        self.client.set_password(password)

    def __del__(self):
        """Destructor (llamado por el GC)"""
        self.disconnect()
        print("🧹 Recursos liberados por __del__")

    # =======================
    # 📡 SUSCRIPCIONES
    # =======================

    def subscribe(self, node_id: str, handler_instance, interval_ms: int = 1000):
        """Suscribe a cambios en un nodo específico."""
        try:
            node = self.client.get_node(node_id)
            if self.subscription is None:
                self.subscription = self.client.create_subscription(interval_ms, handler_instance)

            handle = self.subscription.subscribe_data_change(node)
            self.sub_handles.append(handle)
            print(f"📡 Suscrito a {node_id}")
        except Exception as e:
            print(f"❌ Error al suscribirse a {node_id}: {e}")

    # unsubscribe
    def unsubscribe(self, handle):
        try:
            self.subscription.unsubscribe(handle)
            print(f"📡 Desuscripción {handle} cancelada")
        except Exception as e:
            print(f"❌ Error al cancelar la suscripción {handle}: {e}")

    def _cancel_all_subscriptions(self):
        """Elimina todas las suscripciones activas."""
        if self.subscription:
            for handle in self.sub_handles:
                try:
                    self.subscription.unsubscribe(handle)
                except Exception as e:
                    print(f"⚠️ Error al cancelar suscripción {handle}: {e}")
            try:
                self.subscription.delete()
            except Exception as e:
                print(f"⚠️ Error al eliminar la suscripción: {e}")

            self.subscription = None
            self.sub_handles.clear()

    # =======================
    # 📖 LECTURA / ESCRITURA
    # =======================

    def read(self, node_id, attribute="Value", retrys=3):
        for i in range(retrys):
            try:   
                node = self.client.get_node(node_id)
                if attribute == "Value":
                    return node.get_value()
                elif attribute == "DataType":
                    return node.get_data_type_as_variant_type()
                else:
                    return node.read_attribute(getattr(ua.AttributeIds, attribute))
            except Exception as e:
                print(f"❌ Error al leer {node_id} retry {i}: {e}")
        return None
            
    def write(self, node_id: str, value):
        """Escribe un valor en un nodo OPC."""
        try:
            node = self.client.get_node(node_id)
            node.set_value(value)
            print(f"✅ Escrito {value} en {node_id}")
        except Exception as e:
            print(f"❌ Error al escribir en {node_id}: {e}")

    # get children if there are any
    def get_children(self, node_id: str):
        try:
            node = self.client.get_node(node_id)
            return node.get_children()
        except Exception as e:
            print(f"❌ Error al obtener hijos de {node_id}: {e}")
            return None

    # get node type
    def get_node_info(self, node):
        """Devuelve info básica del nodo: tipo, valor, timestamp, etc."""
        info = {
            "nodeid": node.nodeid.to_string(),
            "type": "Unknown",
            "data_type": None,
            "value": None,
            "server_timestamp": None,
            "name": "Desconocido",
            "has_value": False
        }

        try:
            info["name"] = node.get_display_name().Text
        except:
            pass

        try:
            node_class = node.get_node_class()
            if node_class == ua.NodeClass.Variable:
                info["type"] = "Variable"
                info["data_type"] = str(node.get_data_type_as_variant_type())
                info["value"] = node.get_value()
                info["server_timestamp"] = str(node.read_value().ServerTimestamp)
                info["has_value"] = True
            elif node_class == ua.NodeClass.Object:
                info["type"] = "Object"
            elif node_class == ua.NodeClass.Method:
                info["type"] = "Method"
            elif node_class == ua.NodeClass.Folder:
                info["type"] = "Folder"
            else:
                info["type"] = str(node_class)
        except Exception as e:
            info["error"] = str(e)

        return info
