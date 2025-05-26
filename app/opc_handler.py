from opcua import Client
from flask import current_app
from typing import Optional
from app.database import crud
from app.database.models import db, Item


def int_to_bits(value, bits=16):
    return [(value >> i) & 1 for i in range(bits)]

def bits_from_value(value):
    if not isinstance(value, int):
        return []
    return int_to_bits(value, 32 if abs(value) > 32767 else 16)


class WebAlarmHandler:
    def __init__(self, app):
        self.app = app

    def datachange_notification(self, node, val, data):
        parent_id = node.nodeid.to_string()
        print(f"⚡ Cambio detectado en {parent_id} => {val}")

        try:
            bits = bits_from_value(val)
            with self.app.app_context():
                for i, bit_val in enumerate(bits):
                    bit_node_id = f"{parent_id}[{i}]"
                    item = Item.query.filter_by(node_id=bit_node_id).first()
                    if item:
                        item.estado = str(bit_val)
                        db.session.add(item)
                db.session.commit()
            # get handle and bits
            handle = data.ClientHandle
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
            self._cancel_all_subscriptions()
            if self.is_connected:
                self.client.disconnect()
                print("🔌 Cliente OPC desconectado correctamente")
        except Exception as e:
            print(f"❌ Error al desconectar: {e}")
        finally:
            self.is_connected = False

    def change_endpoint(self, new_endpoint):
        self.endpoint = new_endpoint
        print(f"🔌 Cambiando endpoint a {self.endpoint}")
        print("Usuario:", self.username)
        print("Contraseña:", self.password)
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

    def read(self, node_id: str):
        """Lee el valor actual de un nodo OPC."""
        try:
            node = self.client.get_node(node_id)
            return node.get_value()
        except Exception as e:
            print(f"❌ Error al leer {node_id}: {e}")
            return None

    def write(self, node_id: str, value):
        """Escribe un valor en un nodo OPC."""
        try:
            node = self.client.get_node(node_id)
            node.set_value(value)
            print(f"✅ Escrito {value} en {node_id}")
        except Exception as e:
            print(f"❌ Error al escribir en {node_id}: {e}")
