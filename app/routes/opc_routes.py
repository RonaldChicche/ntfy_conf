from flask import Blueprint, render_template, request, redirect, jsonify, current_app, session, url_for
from app.models import db, Item
from app.config import Config
from app.opc_handler import OpcUaClient, WebAlarmHandler, OPC_CLIENTS
from opcua import ua
from flask_socketio import emit

import json
import os

opc_route = Blueprint('opc_route', __name__)


def int_to_bits(value, bits=16):
    return [(value >> i) & 1 for i in range(bits)]

def get_opc_client(user_key=None):
    # if 'opc_endpoint' not in session:
    #     return None
    # if 'opc_endpoint' in session:
    #     return current_app.config["OPC_CLIENT"]

    if user_key is None and 'opc_endpoint' not in session:
        user_key = session.get("user_id", request.remote_addr)
        return OPC_CLIENTS[user_key]

    if current_app.config.get("OPC_CLIENT") is None:
        client = OpcUaClient(
            session['opc_endpoint'],
            session.get('opc_username'),
            session.get('opc_password')
        )
        client.connect()
        if user_key:
            OPC_CLIENTS[user_key] = client
        current_app.config["OPC_CLIENT"] = client
    
    return current_app.config["OPC_CLIENT"]


def guardar_historial(endpoint):
    historial = cargar_historial()
    if endpoint in historial:
        historial.remove(endpoint)
    historial.insert(0, endpoint)
    historial = historial[:2]  # Solo guardar las 2 más recientes
    with open(Config.HISTORY_FILE, 'w') as f:
        json.dump(historial, f)

def cargar_historial():
    if os.path.exists(Config.HISTORY_FILE):
        try:
            with open(Config.HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

@opc_route.route('/opc/disconnect')
def opc_disconnect():
    client = get_opc_client()
    if client:
        client.disconnect()
        current_app.config["OPC_CLIENT"] = None
    session.clear()
    return redirect(url_for('opc_route.opc_connect'))

@opc_route.route('/opc', methods=['GET', 'POST'])
def opc_connect():
    opc_data = []
    error = None
    connected = False

    if request.method == 'POST':
        endpoint = request.form.get('endpoint')
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_key = request.remote_addr

        current_endpoint = session.get('opc_endpoint')
        current_username = session.get('opc_username')
        current_user_key = session.get('user_id')

        if endpoint != current_endpoint or username != current_username or user_key != current_user_key:
            # Guardar nueva configuración y forzar reconexión
            session['opc_endpoint'] = endpoint
            session['opc_username'] = username
            session['opc_password'] = password
            session["user_id"] = request.remote_addr
            
            guardar_historial(endpoint)

            client = current_app.config.get("OPC_CLIENT")
            if client:
                client.disconnect()
                current_app.config["OPC_CLIENT"] = None

        try:
            client = get_opc_client(user_key=user_key)
            connected = True
        except Exception as e:
            error = str(e)

    # Solo lee nodos si ya está conectado
    client = current_app.config.get("OPC_CLIENT")
    if client:
        try:
            objects = client.client.get_objects_node()
            for obj in objects.get_children():
                print(obj)
                opc_data.append({
                    'name': obj.get_display_name().Text,
                    'nodeid': obj.nodeid.to_string()
                })
            connected = True
        except Exception as e:
            error = str(e)

    return render_template('opc.html', opc_data=opc_data, error=error, connected=connected, endpoint=session.get('opc_endpoint', ''), username=session.get('opc_username', ''))


@opc_route.route('/opc/ver/<path:node_id>')
def opc_ver(node_id):
    from urllib.parse import unquote
    node_id = unquote(node_id)
    client = get_opc_client()
    if not client:
        return redirect(url_for('opc_route.opc_connect'))

    try:
        node = client.client.get_node(node_id)
        name = node.get_display_name().Text
        try:
            data_type = str(node.get_data_type_as_variant_type())
        except:
            data_type = "No disponible"

        try:
            value = node.get_value()
            children = []
        except:
            value = "No legible"
            try:
                children = []
                for child in node.get_children():
                    try:
                        val = child.get_value()
                        dtype = str(child.get_data_type_as_variant_type())
                        try:
                            ts = child.read_value().ServerTimestamp
                        except:
                            ts = None
                        children.append({
                            'name': child.get_display_name().Text,
                            'nodeid': child.nodeid.to_string(),
                            'value': val,
                            'data_type': dtype,
                            'server_timestamp': ts,
                            'has_value': True
                        })
                    except:
                        children.append({
                            'name': child.get_display_name().Text,
                            'nodeid': child.nodeid.to_string(),
                            'has_value': False
                        })
            except:
                children = []

        return render_template(
            'opc_ver.html',
            name=name,
            nodeid=node_id,
            value=value,
            data_type=data_type,
            children=children
        )

    except Exception as e:
        return render_template('opc_ver.html', error=str(e))
    

@opc_route.route('/opc/monitor', methods=['GET', 'POST'])
def monitorear():
    client = get_opc_client()
    if not client:
        return render_template('opc_monitor.html', error="No hay conexión activa con el servidor OPC UA")

    nodos_raiz = []
    subnodos = []
    selected_group = request.form.get('selected_group')
    error = None

    try:
        objects_node = client.client.get_objects_node()
        for child in objects_node.get_children():
            nodos_raiz.append({
                'name': child.get_display_name().Text,
                'nodeid': child.nodeid.to_string()
            })

        if selected_group:
            parent_node = client.client.get_node(selected_group)
            print("PArent node", parent_node)
            for child in parent_node.get_children():
                try:
                    print("Child, ", child)
                    subnodos.append({
                        'name': child.get_display_name().Text,
                        'nodeid': child.nodeid.to_string(),
                        'value': child.get_value()#,
                        #'timestamp': child.read_value().ServerTimestamp
                    })
                    print(subnodos)
                except:
                    continue

    except Exception as e:
        error = str(e)

    return render_template('opc_monitor.html', 
                           nodos_raiz=nodos_raiz,
                           selected_group=selected_group,
                           subnodos=subnodos,
                           error=error)

@opc_route.route('/opc/monitor/json')
def monitoreo_json():
    from urllib.parse import unquote
    client = get_opc_client()
    if not client:
        return jsonify({'error': 'No conectado'}), 400

    group = request.args.get('group')
    if not group:
        return jsonify({'error': 'Falta group'}), 400

    try:
        parent_node = client.client.get_node(unquote(group))
        data = []
        for child in parent_node.get_children():
            try:
                data.append({
                    'name': child.get_display_name().Text,
                    'nodeid': child.nodeid.to_string(),
                    'value': child.get_value()#,
                    #'timestamp': child.read_value().ServerTimestamp.isoformat()
                })
            except:
                continue
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@opc_route.route('/opc/alarms/config', methods=['POST'])
def configurar_alarmas():
    client = get_opc_client()
    if not client:
        return jsonify({'error': 'No hay conexión con el servidor OPC'}), 400

    data = request.get_json()
    if not data or 'nodos' not in data:
        return jsonify({'error': 'Formato de datos inválido'}), 400

    seleccion = data['nodos']
    nodos_validos = []
    errores = []

    print("Seleccion:", seleccion)

    # Obtener los nodos ya suscritos
    suscritos = set()
    if client.subscription:
        for h in client.sub_handles:
            node_id = client.subscription.get_node_id(h)
            suscritos.add(node_id)
    
    # Eliminar los que ya no estan en la seleccion
    for h in client.sub_handles[:]:
        node_id = client.subscription.get_node_id(h)
        if node_id not in suscritos:
            client.subscription.unsubscribe(h)
            client.sub_handles.remove(h)

    for orden, nodo in enumerate(seleccion):
        nodeid = nodo.get("nodeid")
        tipo = nodo.get("type")
        parent_id = nodo.get("parent") or "Desconocido"

        print(f"Orden: {orden}, NodeID: {nodeid}, Parent: {parent_id}, Type: {tipo}")
        if nodeid is None:
            print("descartado")
            continue

        try:
            opc_node = client.client.get_node(nodeid)
            val = opc_node.get_value()
            dtype = opc_node.get_data_type_as_variant_type()
            print("Val:", val, "Dtype:", dtype, "opc_node:", opc_node)

            if dtype not in [ua.VariantType.Int16, ua.VariantType.UInt16, ua.VariantType.Int32, ua.VariantType.UInt32]:
                errores.append({"nodeid": nodeid, "error": f"Tipo no compatible: {dtype.name}"})
                continue

            bits = int_to_bits(val, bits=32 if '32' in dtype.name else 16)
            handle = client.subscription.subscribe_data_change(opc_node)

            print("Handle:", handle, "Bits:", bits)
            client.sub_handles.append(handle)
            nodos_validos.append(nodeid)

            # Guardar un Item por cada bit usando un enumerateinvertido:
            for i, bit in enumerate(bits):
                bit_node_id = f"{nodeid}[{i}]"
                nuevo = Item(
                    node_id=bit_node_id,
                    node_parent=nodeid,
                    estado=str(bit)
                )
                db.session.add(nuevo)

        except Exception as e:
            errores.append({"nodeid": nodeid, "error": str(e)})

    db.session.commit()
    print("✅ Bits registrados como Items:", nodos_validos, 'errores', errores)
    return jsonify({'status': 'ok', 'nodos': nodos_validos, 'errores': errores})


@opc_route.route('/opc/nodes/children', methods=['GET'])
def nodos_children():
    print("🔧 Entró al endpoint de children")

    try:
        from urllib.parse import unquote

        client = get_opc_client()
        print("🔌 Cliente OPC:", client)
        nodeid = request.args.get('nodeid')
        print("🔍 Buscando children de:", nodeid)

        #print("🔧 Buscando cleinte:", session['opc_endpoint'])

        if not client:
            return jsonify({'error': 'Cliente no conectado'}), 400

        if not nodeid:
            return jsonify({'error': 'Parámetro nodeid faltante'}), 400

        node = client.client.get_node(unquote(nodeid))
        children = []
        for child in node.get_children():
            try:
                children.append({
                    'name': child.get_display_name().Text,
                    'nodeid': child.nodeid.to_string()
                })
            except:
                children.append({
                    'name': 'Desconocido',
                    'nodeid': child.nodeid.to_string()
                })
        return jsonify({'children': children})
    except Exception as e:
        return jsonify({'error': str(e)}), 500