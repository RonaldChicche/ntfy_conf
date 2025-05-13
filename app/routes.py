from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import db, Item, Topico, Tipo

import requests

main = Blueprint('main', __name__)

# Items CRUD y manejo

@main.route('/')
def index():
    items = Item.query.all()
    topicos = Topico.query.all()
    tipos = Tipo.query.all()
    return render_template('index.html', items=items, topicos=topicos, tipos=tipos)

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

@main.route('/send', methods=['POST'])
def send_definicion():
    item_id = request.form.get('item_id')

    if not item_id:
        print("❌ No se proporcionó item_id")
        return jsonify({'status': 'error', 'message': 'ID no proporcionado'}), 400

    item = Item.query.get(item_id)
    if not item:
        print(f"❌ Item con ID {item_id} no encontrado")
        return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

    topico = item.topico_rel.topico if item.topico_rel else 'mantenimiento'
    tipo = item.tipo_rel.descripcion if item.tipo_rel else 'mantenimiento'
    mensaje = f"{tipo}: {item.definicion}"

    # 🔍 Para pruebas: muestra lo que se enviaría
    print("📤 MENSAJE A ENVIAR:")
    print("TOPICO:", topico)
    print("CONTENIDO:", mensaje)

    # 🚫 Comentado para pruebas
    # try:
    #     import requests
    #     response = requests.post(Config.NTFY_URL, data=mensaje.encode('utf-8'))
    #     response.raise_for_status()
    #     print("✅ Mensaje enviado a ntfy")
    # except Exception as e:
    #     print(f"❌ Error al enviar notificación: {e}")
    #     return jsonify({'status': 'error', 'message': str(e)}), 500

    return redirect('/')


# Topicos CRUD --------------------------------------------------
@main.route('/topicos')
def ver_topicos():
    topicos = Topico.query.all()
    return render_template('topicos.html', topicos=topicos)

@main.route("/topicos/add", methods=["POST"])
def agregar_topico():
    nombre = request.form["nombre"]
    descripcion = request.form.get("descripcion", "")
    new_topico = Topico(topico=nombre, descripcion=descripcion)
    db.session.add(new_topico)
    db.session.commit()
    return redirect("/topicos")

@main.route("/topicos/delete/<int:id>")
def eliminar_topico(id):
    topico_to_delete = Topico.query.get(id)
    db.session.delete(topico_to_delete)
    db.session.commit()
    return redirect("/topicos")

# Tipos CRUD -----------------------------------------------------
@main.route('/tipos')
def ver_tipos():
    tipos = Tipo.query.all()
    return render_template('tipos.html', tipos=tipos)

@main.route("/tipos/add", methods=["POST"])
def agregar_tipo():
    nombre = request.form["nombre"]
    descripcion = request.form.get("descripcion", "")
    new_tipo = Tipo(tipo=nombre, descripcion=descripcion)
    db.session.add(new_tipo)
    db.session.commit()
    return redirect("/tipos")

@main.route("/tipos/delete/<int:id>")
def eliminar_tipo(id):
    tipo_to_delete = Tipo.query.get(id)
    db.session.delete(tipo_to_delete)
    db.session.commit()
    return redirect("/tipos")