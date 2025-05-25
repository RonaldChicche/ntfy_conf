from opcua import Client

# Conexión al servidor
client = Client("opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator")
client.connect()

try:
    # Nodo que deseas modificar
    # ns=2;s=Tag_Write2 → 20504
    node = client.get_node("ns=2;s=Tag_Write2")  # Asegúrate que sea escribible

    # Valor nuevo a escribir
    nuevo_valor = 20506

    # Escritura
    node.set_value(nuevo_valor)
    print("✅ Valor actualizado con éxito")

finally:
    client.disconnect()
