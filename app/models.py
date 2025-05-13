from app import db  


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(1), nullable=False, default='0')
    
    topico_id = db.Column(
        db.Integer,
        db.ForeignKey('topicos.id', name='fk_items_topico')
    )

    tipo_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos.id', name='fk_items_tipo')
    )

    definicion = db.Column(db.Text)

    # Relaciones para acceder a los objetos relacionados directamente
    topico_rel = db.relationship('Topico', backref='items', lazy=True)
    tipo_rel = db.relationship('Tipo', backref='items', lazy=True)

class Topico(db.Model):
    __tablename__ = 'topicos'
    id = db.Column(db.Integer, primary_key=True)
    topico = db.Column(db.String(3), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

class Tipo(db.Model):
    __tablename__ = 'tipos'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(3), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
