from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func
from app.database.models import Item, TagAsociado, Topico, Tipo, Prioridad

# CRUD Items -----------------------------------------------------
def get_items(db: Session, skip: int = 0):
    # join en cadena: Item → Topico, Tipo → Prioridad
    items = (
        db.query(Item)
        .outerjoin(Item.topico_rel)
        .outerjoin(Item.tipo_rel)
        .outerjoin(Tipo.prioridad)
        .options(
            joinedload(Item.topico_rel),
            joinedload(Item.tipo_rel).joinedload(Tipo.prioridad),
            joinedload(Item.tags_asociados)
        )
        .offset(skip)
        .all()
    )
    return items

def get_item(db: Session, item_id: int):
    return (
        db.query(Item)
        .outerjoin(Item.topico_rel)
        .outerjoin(Item.tipo_rel)
        .outerjoin(Tipo.prioridad)
        .options(
            joinedload(Item.topico_rel),
            joinedload(Item.tipo_rel).joinedload(Tipo.prioridad),
            joinedload(Item.tags_asociados)
        )
        .filter(Item.id == item_id)
        .first()
    )

def get_item_by_order_and_node_id(db: Session, orden: int, node_id: str):
    return (
        db.query(Item)
        .filter(Item.orden == orden)
        .filter(Item.node_id == node_id)
        .first()
    )

# get list of node_id from items only
def get_items_node_id(db: Session, skip: int = 0):
    return db.query(func.distinct(Item.node_id)).offset(skip).all()

def add_item(db: Session, item: Item):
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def delete_items_by_node_id(db: Session, node_id: str):
    count = db.query(Item).filter(Item.node_id == node_id).count()
    db.query(Item).filter(Item.node_id == node_id).delete()
    db.commit()
    return count

# CRUD TagAsociados -----------------------------------------------------
def get_tag_asociados(db: Session, skip: int = 0):
    return db.query(TagAsociado).offset(skip).all()

def add_tag_asociado(db: Session, tag_asociado: TagAsociado):
    db.add(tag_asociado)
    db.commit()
    db.refresh(tag_asociado)
    return tag_asociado

def delete_tag_asociado(db: Session, tag_asociado_id: int):
    tag_asociado = db.query(TagAsociado).filter(TagAsociado.id == tag_asociado_id).first()
    db.delete(tag_asociado)
    db.commit()

def delete_tag_asociados_by_item_id(db: Session, item_id: int):
    db.query(TagAsociado).filter(TagAsociado.item_id == item_id).delete()
    db.commit()

# CRUD Topicos -----------------------------------------------------
def get_topicos(db: Session, skip: int = 0):
    return db.query(Topico).offset(skip).all()

# add topico
def add_topico(db: Session, topico: Topico):
    db.add(topico)
    db.commit()
    db.refresh(topico)
    return topico

# delete topico
def delete_topico(db: Session, topico_id: int):
    topico = db.query(Topico).filter(Topico.id == topico_id).first()
    db.delete(topico)
    db.commit()

# CRUD Tipos -----------------------------------------------------
def get_tipos(db: Session, skip: int = 0):
    return db.query(Tipo).offset(skip).all()

# add tipo
def add_tipo(db: Session, tipo: Tipo):
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo

# delete tipo
def delete_tipo(db: Session, tipo_id: int):
    tipo = db.query(Tipo).filter(Tipo.id == tipo_id).first()
    db.delete(tipo)
    db.commit()

# update tipo
def update_tipo(db: Session, tipo_id: int, tipo: Tipo):
    db.query(Tipo).filter(Tipo.id == tipo_id).update(tipo)
    db.commit()

# CRUD Prioridades -----------------------------------------------------
def get_prioridades(db: Session, skip: int = 0):
    return db.query(Prioridad).offset(skip).all()

# add prioridad
def add_prioridad(db: Session, prioridad: Prioridad):
    db.add(prioridad)
    db.commit()
    db.refresh(prioridad)
    return prioridad

# delete all prioridades
def delete_prioridades(db: Session):
    db.query(Prioridad).delete()
    db.commit()

