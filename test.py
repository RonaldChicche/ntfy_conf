from opcua import Client
from datetime import datetime, timedelta, timezone

endpoint = "opc.tcp://localhost:62640/IntegrationObjects/ServerSimulator"
nodeid = "ns=2;s=1:Tag11"  # Nodo ya historizado

client = Client(endpoint)
try:
    client.connect()
    node = client.get_node(nodeid)
    now_local = datetime.now().astimezone()
    print(f"🕒 Ejecutando script a las: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Usa hora local del sistema (sin tzinfo forzado)
    start_time_local = datetime(2025, 5, 16, 10, 42, 0)  # <-- tu hora local
    end_time_local = datetime(2025, 5, 16, 10, 43, 0)

    # Convertir a UTC para la solicitud OPC UA (obligatorio para que el servidor lo entienda)
    start_time = start_time_local.astimezone().astimezone(timezone.utc)
    end_time = end_time_local.astimezone().astimezone(timezone.utc)

    print(f"📅 Leyendo historial desde {start_time} hasta {end_time}")
    datos = node.read_raw_history(start_time, end_time)

    if datos:
        for d in datos:
            ts = d.SourceTimestamp.strftime('%Y-%m-%d %H:%M:%S')
            val = d.Value.Value
            print(f"🕒 {ts} | 📈 Valor: {val} | ✅ Estado: {d.StatusCode.name}")
    else:
        print("⚠️ No se encontraron datos históricos.")

finally:
    client.disconnect()
    print("🔌 Desconectado")
