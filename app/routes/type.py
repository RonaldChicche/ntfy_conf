from flask import Blueprint, render_template, request, redirect
from app.models import db, Tipo, Prioridad


type_route = Blueprint('type_route', __name__)

# Tipos CRUD -----------------------------------------------------
@type_route.route('/tipos')
def ver_tipos():
    tipos = Tipo.query.all()
    prioridades = Prioridad.query.all()
    return render_template('tipos.html', tipos=tipos, prioridades=prioridades)

@type_route.route("/tipos/add", methods=["POST"])
def agregar_tipo():
    nombre = request.form["nombre"]
    descripcion = request.form.get("descripcion", "")
    prioridad_id = request.form.get("prioridad_id", type=int)

    new_tipo = Tipo(tipo=nombre, descripcion=descripcion, prioridad_id=prioridad_id)
    db.session.add(new_tipo)
    db.session.commit()
    return redirect("/tipos")

@type_route.route("/tipos/delete/<int:id>")
def eliminar_tipo(id):
    tipo_to_delete = Tipo.query.get(id)
    db.session.delete(tipo_to_delete)
    db.session.commit()
    return redirect("/tipos")

@type_route.route("/tipos/update/<int:id>", methods=["POST"])
def actualizar_tipo(id):
    tipo = Tipo.query.get_or_404(id)

    tipo.tipo = request.form.get("nombre", tipo.tipo)
    tipo.descripcion = request.form.get("descripcion", tipo.descripcion)
    tipo.prioridad_id = request.form.get("prioridad_id", type=int)

    db.session.commit()
    return redirect("/tipos")

@type_route.route("/tipos/update_prioridad/<int:id>", methods=["POST"])
def actualizar_prioridad_tipo(id):
    tipo = Tipo.query.get_or_404(id)
    nueva_prioridad = request.form.get("prioridad_id", type=int)

    tipo.prioridad_id = nueva_prioridad
    db.session.commit()
    return redirect("/tipos")
