from flask import Blueprint, render_template, request, redirect
from app.models import db, Topico, Prioridad


topic = Blueprint('topic', __name__)


# Topicos CRUD --------------------------------------------------
@topic.route('/topicos')
def ver_topicos():
    topicos = Topico.query.all()
    prioridades = Prioridad.query.all()
    return render_template('topicos.html', topicos=topicos, prioridades=prioridades)

@topic.route("/topicos/add", methods=["POST"])
def agregar_topico():
    nombre = request.form["nombre"]
    descripcion = request.form.get("descripcion", "")
    new_topico = Topico(topico=nombre, descripcion=descripcion)
    db.session.add(new_topico)
    db.session.commit()
    return redirect("/topicos")

@topic.route("/topicos/delete/<int:id>")
def eliminar_topico(id):
    topico_to_delete = Topico.query.get(id)
    db.session.delete(topico_to_delete)
    db.session.commit()
    return redirect("/topicos")