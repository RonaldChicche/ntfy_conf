from opcua import Client

# URL del servidor desde la interfaz que mostraste
url = "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator"

# Crear cliente y conectar
client = Client(url)
try:
    client.connect()
    print("✅ Conectado al servidor OPC UA")

    # Obtener el nodo raíz
    root = client.get_root_node()
    print("🔍 Nodo raíz:", root)

    # Navegar algunos niveles del árbol
    objects = client.get_objects_node()
    print("📦 Objetos disponibles:")
    for child in objects.get_children():
        print(" -", child, "=>", child.get_display_name().Text)

    # OPCIONAL: leer un valor si conoces el NodeId
    # node = client.get_node("ns=2;s=SimulationExamples.FunctionGenerator1.Sine")
    # value = node.get_value()
    # print("📈 Valor de la variable:", value)

    realtime = client.get_node("ns=2;s=Realtimedata")
    for var in realtime.get_children():
        print(var, "=>", var.get_display_name().Text, var.get_value())

finally:
    client.disconnect()
    print("🔌 Desconectado")
