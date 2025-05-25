from opcua import Client
import time

# Dirección del servidor y nodo a suscribirse
url = "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator"
node_id = "ns=2;s=Tag1"

# Manejador para eventos de suscripción
class MySubHandler:
    def datachange_notification(self, node, val, data):
        print(f"🟡 Nuevo valor detectado en {node}: {val}")

# Crear cliente OPC UA
client = Client(url)

try:
    client.connect()
    print("✅ Conectado al servidor OPC UA")

    # Obtener nodo
    node = client.get_node(node_id)

    # Crear suscripción
    handler = MySubHandler()
    sub = client.create_subscription(1000, handler)
    handle = sub.subscribe_data_change(node)

    print(f"📡 Escuchando cambios en {node_id}... (Ctrl + C para salir)")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Ctrl + C detectado. Cerrando sesión...")
    sub.unsubscribe(handle)
    sub.delete()
    client.disconnect()
    print("🔌 Desconectado del servidor OPC UA")

except Exception as e:
    print(f"❌ Error: {e}")
    client.disconnect()

