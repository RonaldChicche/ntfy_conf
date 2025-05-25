from opcua import Client
from opcua.common.subscription import SubscriptionHandler
import requests

# Configuración
OPC_SERVER_URL = "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator"
NTFY_TOPIC = "mytopic"  # <- Cambia por el topic que uses

# Cliente OPC
client = Client(OPC_SERVER_URL)

# Clase manejadora de cambios
class SubHandler(SubscriptionHandler):
    def datachange_notification(self, node, val, data):
        print(f"🔄 Cambio en {node}: {val}")
        message = f"⚠️ Alerta OPC: {node.get_display_name().Text} cambió a {val}"
        try:
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode("utf-8"))
            print("📲 Notificación enviada")
        except Exception as e:
            print("❌ Error al enviar notificación:", e)

try:
    client.connect()
    print("✅ Conectado a OPC UA")

    # Obtener nodo específico
    tag_node = client.get_node("ns=2;s=Tag1")

    # Crear suscripción
    handler = SubHandler()
    subscription = client.create_subscription(1000, handler)  # cada 1s
    handle = subscription.subscribe_data_change(tag_node)

    print("📡 Escuchando cambios en Tag1... (Ctrl+C para salir)")
    while True:
        pass

except KeyboardInterrupt:
    print("🛑 Interrumpido por usuario")

finally:
    client.disconnect()
    print("🔌 Desconectado del servidor OPC")
