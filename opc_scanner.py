
# no Funciona todavia


import socket
from opcua import Client
from opcua.ua.uaerrors import UaStatusCodeError
import concurrent.futures

# Configura tu subred
subnet = "192.168.1."  # ← Cambia esto según tu red local
ports = [4840, 62541]  # Puertos comunes para OPC UA
timeout = 0.5  # segundos

def is_opcua_server(ip, port):
    url = f"opc.tcp://{ip}:{port}"
    try:
        # Verifica si el puerto está abierto
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        sock.close()

        # Verifica si responde como servidor OPC UA
        client = Client(url)
        client.set_timeout(1)
        client.connect()
        client.get_root_node()  # fuerza handshake
        client.disconnect()
        return url
    except:
        return None

def scan_subnet():
    print(f"🔍 Escaneando la red {subnet}0/24...")
    ips = [f"{subnet}{i}" for i in range(1, 255)]
    tasks = [(ip, port) for ip in ips for port in ports]
    found = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(is_opcua_server, ip, port) for ip, port in tasks]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                print(f"✅ Servidor OPC UA encontrado: {result}")
                found.append(result)
    
    return found

if __name__ == "__main__":
    servidores = scan_subnet()
    print("\n📋 Lista de servidores encontrados:")
    for s in servidores:
        print(" -", s)
