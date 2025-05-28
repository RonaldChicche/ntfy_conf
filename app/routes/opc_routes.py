from flask import Blueprint, render_template, request, redirect, jsonify, current_app, session, url_for
from app.database.models import db, Item
from app.database import crud
from app.config import get_config_value, set_config_value
from app.opc_handler import OpcUaClient, WebAlarmHandler, bits_from_value
from opcua import ua
from urllib.parse import unquote
import json
#from app import OPC_CLIENT

opc_route = Blueprint('opc_route', __name__)
opc_client = OpcUaClient(get_config_value('OPC_SERVER_URL'), get_config_value('OPC_USER'), get_config_value('OPC_PASSWORD'))
opc_client.connect()
#opc_client.restore_subscriptions()

@opc_route.route('/send', methods=['POST'])
def send_definicion():
    item_id = request.form.get('item_id') or (request.json or {}).get('item_id')
    if not item_id:
        print("❌ No se proporcionó item_id")
        return jsonify({'status': 'error', 'message': 'ID no proporcionado'}), 400

    item = crud.get_item(db.session, item_id)
    if not item:
        return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

    # Tags asociados 
    tags_info = []
    if item.tags_asociados:
        for tag in item.tags_asociados:
            value = opc_client.read(tag.direccion, "Value")
            tags_info.append((tag.nombre, tag.direccion, value))
    
    lecturas_str = "Lectura:\n\tSin lecturas disponibles" if not tags_info else \
        "Lectura:\n" + "\n".join([
            f"\t{nombre} ({direccion})\t\t{valor}"
            for nombre, direccion, valor in tags_info
        ])

    mensaje = item.definicion
    if lecturas_str:
        mensaje += "\n\n" + lecturas_str

    payload = {
        "topic": item.topico_rel.descripcion if item.topico_rel else 'mantenimiento',
        "message": mensaje,
        "title": item.tipo_rel.descripcion if item.tipo_rel else "Notificación",
        "priority": item.tipo_rel.prioridad_id if item.tipo_rel else 0
    }

    print("📤 JSON A ENVIAR:")
    print(json.dumps(payload, indent=2))

    # Envío opcional (comentado para pruebas)
    # try:
    #     import requests
    #     response = requests.post(get_config_value("NTFY_URL"), json=payload)
    #     response.raise_for_status()
    #     print("✅ Mensaje enviado a ntfy")
    # except Exception as e:
    #     print(f"❌ Error al enviar notificación: {e}")
    #     return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'success', 'message': 'Mensaje enviado'}), 200

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
    opc_client.restore_subscriptions()
    return redirect(url_for('opc_route.opc_main'))

@opc_route.route('/opc/disconnect')
def opc_disconnect():
    # cierra conexion
    opc_client.disconnect()
    return redirect(url_for('opc_route.opc_main'))

# restore subscriptions
@opc_route.route('/opc/restore')
def opc_restore():
    result = opc_client.restore_subscriptions()
    return result

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
        node_info = opc_client.get_node_info(node)  # ← aquí usamos el método de la clase

        children = []
        for child in node.get_children():
            info = opc_client.get_node_info(child)
            children.append(info)

    except Exception as e:
        return render_template('opc_ver.html', error=str(e))

    return render_template(
        'opc_ver.html',
        name=node_info.get("name", "Sin nombre"),
        nodeid=node_info["nodeid"],
        value=node_info.get("value"),
        data_type=node_info.get("data_type", "N/A"),
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
            print("Parent node", parent_node)
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

    # cargar nodos ya registrados como alarmas
    alarmas_raw = crud.get_items_node_id(db.session, skip=0)
    alarmas = [{"node_id": nodo[0]} for nodo in alarmas_raw]

    return render_template('opc_monitor.html', 
                           nodos_raiz=nodos_raiz,
                           selected_group=selected_group,
                           subnodos=subnodos,
                           error=error,
                           alarmas=alarmas)

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
    
    # get node parent from nodes
    node_parent = get_config_value("TAGS_NODE")

    nodos_enviados = [n.get("nodeid") for n in data['nodos'] if n.get("nodeid")]
    nodos_config = get_config_value("TAGS_SUBSCRIBE") or []

    nodos_crear = list(set(nodos_enviados) - set(nodos_config))
    nodos_eliminar = list(set(nodos_config) - set(nodos_enviados))

    handler = WebAlarmHandler(app=current_app._get_current_object())
    errores = []

    # 1. Eliminar de la DB los nodos ya no usados
    for nodo in nodos_eliminar:
        try:
            print(f"Eliminando nodo {nodo}")
            deleted = crud.delete_items_by_node_id(db.session, nodo)
            print(f"|__> Items eliminados: {deleted}")
        except Exception as e:
            errores.append({"nodeid": nodo, "error": f"Error al eliminar: {e}"})

    # 2. Validar y crear solo los nuevos nodos
    for nodo in nodos_crear:
        try:
            node = opc_client.client.get_node(nodo)
            dtype = node.get_data_type_as_variant_type()

            if dtype not in [ua.VariantType.Int16, ua.VariantType.UInt16,
                             ua.VariantType.Int32, ua.VariantType.UInt32]:
                errores.append({"nodeid": nodo, "error": f"Tipo no compatible: {dtype.name}"})
                continue

            val = node.get_value()
            bits = bits_from_value(val)

            for i, bit_val in enumerate(bits):
                item = Item(
                    node_id=nodo,
                    node_parent=node_parent,
                    estado=str(bit_val),
                    definicion=f"Bit {i} de {nodo}",
                    orden=i
                )
                db.session.add(item)

        except Exception as e:
            errores.append({"nodeid": nodo, "error": str(e)})

    db.session.commit()

    # 3. Cancelar todas las suscripciones OPC y rehacerlas con todos los nodos enviados
    opc_client._cancel_all_subscriptions()
    for nodo in nodos_enviados:
        try:
            opc_client.subscribe(nodo, handler)
        except Exception as e:
            errores.append({"nodeid": nodo, "error": f"No se pudo suscribir: {e}"})

    # 4. Guardar en config.json la nueva lista completa
    set_config_value("TAGS_SUBSCRIBE", nodos_enviados)

    return jsonify({
        'status': 'ok',
        'nodos_enviados': nodos_enviados,
        'nodos_creados': nodos_crear,
        'nodos_eliminados': nodos_eliminar,
        'errores': errores
    })


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