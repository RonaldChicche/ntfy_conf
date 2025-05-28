from app import db  


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    node_parent = db.Column(db.String(20), nullable=False)
    node_id = db.Column(db.String(20), nullable=False)
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

    # orden -> integer, valor unico, no nullo , dedfault id
    orden = db.Column(db.Integer, nullable=False, default=id)

    # Relaciones para acceder a los objetos relacionados directamente
    tags_asociados = db.relationship('TagAsociado', backref='item', lazy=True)
    topico_rel = db.relationship('Topico', backref='items', lazy=True)
    tipo_rel = db.relationship('Tipo', backref='items', lazy=True)
    definicion = db.Column(db.Text)

class TagAsociado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20))  
    direccion = db.Column(db.String(20), unique=True, nullable=False)  
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)  # asociación con Item

class Topico(db.Model):
    __tablename__ = 'topicos'
    id = db.Column(db.Integer, primary_key=True)
    topico = db.Column(db.String(3), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

class Tipo(db.Model):
    __tablename__ = 'tipos'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(3), unique=True, nullable=False)
    prioridad_id = db.Column(db.Integer, db.ForeignKey('prioridades.id'), nullable=False)
    descripcion = db.Column(db.Text)
    
    prioridad = db.relationship('Prioridad')

class Prioridad(db.Model):
    __tablename__ = 'prioridades'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20), nullable=False)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(50), nullable=True)  # nombre de ícono (opcional)