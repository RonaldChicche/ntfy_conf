from app import db  


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(1), nullable=False, default='0')
    topico = db.Column(db.String(2), db.ForeignKey('topicos.topico'))
    tipo = db.Column(db.String(2), db.ForeignKey('tipos.nombre'))
    definicion = db.Column(db.Text)

class Topico(db.Model):
    __tablename__ = 'topicos'
    id = db.Column(db.Integer, primary_key=True)
    topico = db.Column(db.String, unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    # Relación inversa (opcional si quieres acceder a los items desde aquí)
    items = db.relationship('Item', backref='topico_rel', lazy=True)

class Tipo(db.Model):
    __tablename__ = 'tipos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    items = db.relationship('Item', backref='tipo_rel', lazy=True)
