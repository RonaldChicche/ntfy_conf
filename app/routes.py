from flask import Blueprint, render_template, request, redirect, url_for
from app.models import db, Item, Topico, Tipo

main = Blueprint('main', __name__)

# Items CRUD y manejo

@main.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)

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
    new_def = request.form.get('new_definicion', '')
    item = Item.query.get(item_id)  
    if item:
        item.definicion = new_def  
        db.session.commit()  
        return jsonify({'status': 'ok', 'id': item_id, 'new_definicion': new_def})
    return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

@main.route('/item/topico/<int:item_id>', methods=['POST'])
def update_item_topico(item_id):
    topico = request.form.get('topico')
    item = Item.query.get(item_id)  
    if item:
        item.topico = topico  
        db.session.commit() 
        return redirect('/')  
    return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404

@main.route('/item/tipo/<int:item_id>', methods=['POST'])
def update_item_tipo(item_id):
    tipo = request.form.get('tipo')
    item = Item.query.get(item_id)  
    if item:
        item.tipo = tipo  
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


# @app.route('/send', methods=['POST'])
# def send_msg():
#     definicion = request.form.get('definicion', '').strip()
#     topico = 'mantenimiento'
#     print(f"{NTFY_URL}{topico}", "--->", definicion)
#     try:
#         r = requests.post(f"{NTFY_URL}{topico}", data=definicion.encode('utf-8'))
#         r.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         return jsonify({'error': str(e)}), 500

#     return jsonify({'status': 'mensaje enviado', 'topico': topico}), 200

@main.route('/send', methods=['POST'])
def send_definicion():
    item_id = request.form.get('item_id')
    item = Item.query.get(item_id)

    if item:
        topico = item.topico or 'mantenimiento'
        mensaje = f"{topico}: {item.definicion}"
        print(topico, mensaje)

        try:
            requests.post(Config.NTFY_URL, data=mensaje.encode('utf-8'))
        except Exception as e:
            print(f"Error al enviar notificación: {e}")

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
    new_topico = Topico(nombre_topico=nombre, descripcion=descripcion)
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
    new_tipo = Tipo(nombre_tipo=nombre, descripcion=descripcion)
    db.session.add(new_tipo)
    db.session.commit()
    return redirect("/tipos")

@main.route("/tipos/delete/<int:id>")
def eliminar_tipo(id):
    tipo_to_delete = Tipo.query.get(id)
    db.session.delete(tipo_to_delete)
    db.session.commit()
    return redirect("/tipos")