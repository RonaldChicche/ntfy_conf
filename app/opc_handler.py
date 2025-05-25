from flask import current_app
from opcua import Client
from app.models import db, Item
#from app import socketio

OPC_CLIENTS = {}


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
        from app.models import Item
        from app import db

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
        except Exception as e:
            print("❌ Error actualizando bits:", e)


class OpcUaClient:
    def __init__(self, endpoint, username=None, password=None):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.client = Client(endpoint)
        if username and password:
            self.client.set_user(username)
            self.client.set_password(password)
        self.subscription = None
        self.sub_handles = []
        self.is_connected = False

    def __del__(self):
        # Este método se ejecuta cuando el objeto es recolectado por el GC
        if self.is_connected:
            self.disconnect()
        print("🔌 Cliente OPC desconectado desde __del__")

    def connect(self):
        try:
            self.client.connect()
            self.is_connected = True
            print("✅ Conectado exitosamente")
        except Exception as e:
            print(f"❌ Error al conectar: {e}")

    def disconnect(self):
        try:
            # Cierra suscripciones si existen
            if self.subscription:
                for h in self.sub_handles:
                    try:
                        self.subscription.unsubscribe(h)
                    except Exception as e:
                        print(f"⚠️ No se pudo cancelar suscripción {h}: {e}")
                try:
                    self.subscription.delete()
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar la suscripción: {e}")
                self.subscription = None
                self.sub_handles = []

            # Solo intenta desconectar si está conectado
            if self.is_connected:
                try:
                    self.client.disconnect()
                    print("🔌 Cliente OPC desconectado correctamente")
                except Exception as e:
                    print(f"⚠️ Error al desconectar el cliente: {e}")
                self.is_connected = False

        except Exception as general_error:
            print(f"❌ Error general al cerrar cliente OPC: {general_error}")


    def read(self, node_id):
        node = self.client.get_node(node_id)
        return node.get_value()

    def write(self, node_id, value):
        node = self.client.get_node(node_id)
        node.set_value(value)

    def subscribe(self, node_id, handler_class, interval_ms=1000):
        node = self.client.get_node(node_id)
        if not self.subscription:
            self.subscription = self.client.create_subscription(interval_ms, handler_class)
        handle = self.subscription.subscribe_data_change(node)
        self.sub_handles.append(handle)
