from opcua import Client, ua
from datetime import datetime, timedelta, timezone

# OPC UA endpoint
endpoint = "opc.tcp://localhost:62640/IntegrationObjects/ServerSimulator"  # ajusta si es necesario
#nodeid_ha_config = "ns=2;s=Tag10?HA Configuration"  # usa el que corresponda a tu nodo
nodeid_ha_config = "ns=2;s=Historicaldata"
# Crear cliente
client = Client(endpoint)

now = datetime.now(timezone.utc)

config_values = {
    "Stepped": True,
    "Definition": "Histórico de prueba",
    "MaxTimeInterval": 1.0,
    "MinTimeInterval": 0.0,
    "ExceptionDeviation": 0.0,
    "ExceptionDeviationFormat": 0,
    "StartOfArchive": now,
    "StartOfOnlineArchive": now,
}

try:
    client.connect()
    print("✅ Conectado")

    # Obtener el nodo HA Configuration
    ha_config_node = client.get_node(nodeid_ha_config)

    # Leer y mostrar hijos configurables
    children = ha_config_node.get_children()
    for child in children:
        name = child.get_display_name().Text
        print(f"🔧 Subnodo: {name} => {child.nodeid}")
        if name == "Tag8":
            tag_node = child
            break

    # Acceso a : Subnodo: Tag8 => StringNodeId(ns=2;s=1:Tag8)
    ha_node = None
    for subchild in tag_node.get_children():
        name = subchild.get_display_name().Text
        print(f"  ↳ {name}")
        if "HA" in name:
            ha_node = subchild

    for child in ha_node.get_children():
        name = child.get_display_name().Text
        if name in config_values:
            try:
                print(f"🛠 Seteando {name} => {config_values[name]}")
                child.set_value(config_values[name])
            except Exception as e:
                print(f"❌ Error al configurar {name}: {e}")
    
    # tratando de leer historial: 
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=5)
    print("Fechas:", start_time, end_time)

    hist_data = tag_node.read_raw_history(starttime=start_time, endtime=end_time, numvalues=10)

    for d in hist_data:
        print(f"📅 {d.SourceTimestamp} | 📈 {d.Value.Value} | ✅ {d.StatusCode.name}")


    print("✅ Configuración aplicada.")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    client.disconnect()
    print("🔌 Desconectado")
