from flask import Blueprint, render_template, request, redirect, jsonify, url_for, current_app
from app.database.models import db, Item, Topico, Tipo, Prioridad, TagAsociado
from app.database import crud
from app.config import get_config_value

import json
import requests

main = Blueprint('main', __name__)


def get_tags():
    # Obtener el nodo raíz desde la configuración
    tags_node = get_config_value("TAGS_NODE")
    print ("tags_node", tags_node)
    if not tags_node:
        return []

    # Llamar a la API local para obtener los nodos hijos
    try:
        base_url = current_app.config.get("BASE_URL", "http://localhost:5000")  # Cambia puerto si necesario
        print("base_url", base_url)
        response = requests.get(f"{base_url}/opc/nodes/children?nodeid={tags_node}")
        if response.status_code == 200:
            data = response.json()
            print("data", data)
            return data.get("children", [])
        else:
            current_app.logger.error(f"Error al obtener tags OPC: {response.status_code} {response.text}")
            return []
    except Exception as e:
        current_app.logger.error(f"Excepción en get_tags(): {e}")
        return []

# Items CRUD y manejo

@main.route('/')
def index():
    items = crud.get_items(db.session)
    topicos = crud.get_topicos(db.session)
    tipos = crud.get_tipos(db.session)
    prioridades = crud.get_prioridades(db.session)
    tags = crud.get_tag_asociados(db.session)
    all_tags = get_tags()
    print("---->>>>>> TAGS :", all_tags)
    return render_template('index.html', items=items, topicos=topicos, tipos=tipos, prioridades=prioridades, tags=tags, all_tags=all_tags)

@main.route('/add', methods=['POST'])
def add_item():
    definicion = request.form['definicion']
    item = Item(definicion=definicion)
    db.session.add(item)
    db.session.commit()
    return redirect('/')

@main.route('/delete_item/<int:id>')
def delete_item(id):
    item_to_delete = Item.query.get(id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect('/')

@main.route('/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    item = Item.query.get(item_id)
    if item:
        item.definicion = request.form.get('new_definicion', item.definicion)
        item.estado = '1' if request.form.get('estado') == '1' else '0'
        item.topico_id = int(request.form.get('topico_id')) if request.form.get('topico_id') else None
        item.tipo_id = int(request.form.get('tipo_id')) if request.form.get('tipo_id') else None
        db.session.commit()
        return redirect('/')
    return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

@main.route('/item/topico/<int:item_id>', methods=['POST'])
def update_item_topico(item_id):
    topico_id = request.form.get('topico_id')
    item = Item.query.get(item_id)  
    if item:
        item.topico_id = int(topico_id) if topico_id else None
        db.session.commit()
        return redirect('/') 
    return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

@main.route('/item/tipo/<int:item_id>', methods=['POST'])
def update_item_tipo(item_id):
    tipo_id = request.form.get('tipo_id')
    item = Item.query.get(item_id)  
    if item:
        item.tipo_id = int(tipo_id) if tipo_id else None  
        db.session.commit()  
        return redirect('/')  
    return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

@main.route('/change/<int:item_id>', methods=['POST'])
def change_item(item_id):
    state = int(request.form['estado'])
    new_state = 0 if state == 1 else 1
    
    # Buscar el item por ID usando SQLAlchemy
    item = Item.query.get(item_id)
    
    if item:
        item.estado = new_state  # Actualizar el estado del item
        db.session.commit()  # Guardar los cambios en la base de datos
        return redirect('/')  # Redirigir a la página principal
    else:
        return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404



@main.route('/items/json')
def items_json():
    items = crud.get_items(db.session)
    #print("items", items)
    return jsonify([{"id": item.id, "estado": item.estado} for item in items])

@main.route("/item/<int:item_id>/tags/update", methods=["POST"])
def update_tags(item_id):
    item = Item.query.get_or_404(item_id)
    nuevas = set(request.form.getlist("tags"))
    print(f"🔍 Nuevas tags: {nuevas}")

    # Eliminar los que ya no están
    for t in item.tags_asociados[:]:
        if t.direccion not in nuevas:
            db.session.delete(t)

    # Agregar nuevos
    existentes = {t.direccion for t in item.tags_asociados}
    for direccion in nuevas - existentes:
        nuevo_tag = TagAsociado(nombre="Nuevo", direccion=direccion, item_id=item.id)
        db.session.add(nuevo_tag)

    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/tags/<int:tag_id>/update", methods=["POST"])
def update_tag_nombre(tag_id):
    tag = TagAsociado.query.get_or_404(tag_id)
    nuevo_nombre = request.form.get("nombre")
    if nuevo_nombre:
        tag.nombre = nuevo_nombre
        db.session.commit()
    return redirect(url_for("main.index"))


