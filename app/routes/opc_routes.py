from flask import Blueprint, render_template, request, redirect, jsonify, current_app, session, url_for
from app.database.models import db, Item
from app.config import get_config_value
from app.opc_handler import OpcUaClient, WebAlarmHandler
from opcua import ua
from urllib.parse import unquote

import json
import os

opc_route = Blueprint('opc_route', __name__)
opc_client = OpcUaClient(get_config_value('OPC_ENDPOINT'), get_config_value('OPC_USERNAME'), get_config_value('OPC_PASSWORD'))


@opc_route.route('/opc/connect', methods=['POST'])
def opc_connect():
    # recibe credenciales
    endpoint = request.form.get('endpoint')
    username = request.form.get('username')
    password = request.form.get('password')

    # compara credenciales
    if endpoint != opc_client.endpoint or username != opc_client.username or password != opc_client.password:
        opc_client.change_credentials(username, password)
        opc_client.change_endpoint(endpoint)
        return redirect(url_for('opc_route.opc_main'))

    # inicia conexion
    opc_client.connect()
    return redirect(url_for('opc_route.opc_main'))

@opc_route.route('/opc/disconnect')
def opc_disconnect():
    # cierra conexion
    opc_client.disconnect()
    return redirect(url_for('opc_route.opc_main'))

@opc_route.route('/opc')
def opc_main():
    opc_data = []
    error = None
    connected = False

    # Solo lee nodos si ya está conectado
    if opc_client.is_connected:
        try:
            objects = opc_client.client.get_objects_node()
            for obj in objects.get_children():
                opc_data.append({
                    'name': obj.get_display_name().Text,
                    'nodeid': obj.nodeid.to_string()
                })
            connected = True
        except Exception as e:
            error = str(e)

    return render_template( 'opc.html', 
                           opc_data=opc_data, error=error, 
                           connected=connected, 
                           endpoint=opc_client.endpoint, 
                           username=opc_client.username)


@opc_route.route('/opc/ver/<path:node_id>')
def opc_ver(node_id):
    node_id = unquote(node_id)
    if not opc_client.is_connected:
        return redirect(url_for('opc_route.opc_main'))

    try:
        node = opc_client.client.get_node(node_id)
        name = node.get_display_name().Text
        data_type = str(node.get_data_type_as_variant_type())
        value = node.get_value()
        children = []
        for child in node.get_children():
            val = child.get_value()
            dtype = str(child.get_data_type_as_variant_type())
            ts = child.read_value().ServerTimestamp
            children.append({
                'name': child.get_display_name().Text,
                'nodeid': child.nodeid.to_string(),
                'value': val,
                'data_type': dtype,
                'server_timestamp': ts,
                'has_value': True
            })
    except Exception as e:
        return render_template('opc_ver.html', error=str(e))
    
    return render_template(
            'opc_ver.html',
            name=name,
            nodeid=node_id,
            value=value,
            data_type=data_type,
            children=children
        )

@opc_route.route('/opc/monitor', methods=['GET', 'POST'])
def monitorear():
    if not opc_client.is_connected:
        return render_template('opc_monitor.html', error="No hay conexión activa con el servidor OPC UA")

    nodos_raiz = []
    subnodos = []
    selected_group = request.form.get('selected_group')
    error = None

    try:
        objects_node = opc_client.client.get_objects_node()
        for child in objects_node.get_children():
            nodos_raiz.append({
                'name': child.get_display_name().Text,
                'nodeid': child.nodeid.to_string()
            })

        if selected_group:
            parent_node = opc_client.client.get_node(selected_group)
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
    if not opc_client.is_connected:
        return jsonify({'error': 'No conectado'}), 400

    group = request.args.get('group')
    if not group:
        return jsonify({'error': 'Falta group'}), 400

    try:
        parent_node = opc_client.client.get_node(unquote(group))
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
    if not opc_client.is_connected:
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
    if opc_client.subscription:
        for h in opc_client.sub_handles:
            node_id = opc_client.subscription.get_node_id(h)
            suscritos.add(node_id)
    
    # Eliminar los que ya no estan en la seleccion
    for h in opc_client.sub_handles[:]:
        node_id = opc_client.subscription.get_node_id(h)
        if node_id not in suscritos:
            opc_client.subscription.unsubscribe(h)
            opc_client.sub_handles.remove(h)

    for orden, nodo in enumerate(seleccion):
        nodeid = nodo.get("nodeid")
        tipo = nodo.get("type")
        parent_id = nodo.get("parent") or "Desconocido"

        print(f"Orden: {orden}, NodeID: {nodeid}, Parent: {parent_id}, Type: {tipo}")
        if nodeid is None:
            print("descartado")
            continue

        try:
            opc_node = opc_client.client.get_node(nodeid)
            val = opc_node.get_value()
            dtype = opc_node.get_data_type_as_variant_type()
            print("Val:", val, "Dtype:", dtype, "opc_node:", opc_node)

            if dtype not in [ua.VariantType.Int16, ua.VariantType.UInt16, ua.VariantType.Int32, ua.VariantType.UInt32]:
                errores.append({"nodeid": nodeid, "error": f"Tipo no compatible: {dtype.name}"})
                continue

            #bits = int_to_bits(val, bits=32 if '32' in dtype.name else 16)
            handle = opc_client.subscription.subscribe_data_change(opc_node)
            opc_client.sub_handles.append(handle)
            nodos_validos.append(nodeid)

        except Exception as e:
            errores.append({"nodeid": nodeid, "error": str(e)})

    db.session.commit()
    print("✅ Bits registrados como Items:", nodos_validos, 'errores', errores)
    return jsonify({'status': 'ok', 'nodos': nodos_validos, 'errores': errores})


@opc_route.route('/opc/nodes/children', methods=['GET'])
def nodos_children():
    print("🔧 Entró al endpoint de children")

    try:
        nodeid = request.args.get('nodeid')
        print("🔍 Buscando children de:", nodeid)

        #print("🔧 Buscando cleinte:", session['opc_endpoint'])

        if not opc_client.is_connected:
            return jsonify({'error': 'Cliente no conectado'}), 400

        if not nodeid:
            return jsonify({'error': 'Parámetro nodeid faltante'}), 400

        node = opc_client.client.get_node(unquote(nodeid))
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