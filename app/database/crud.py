from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database.models import Item, TagAsociado, Topico, Tipo, Prioridad

# CRUD Items -----------------------------------------------------
def get_items(db: Session, skip: int = 0):
    # join en cadena: Item → Topico, Tipo → Prioridad
    items = (
        db.query(Item)
        .join(Item.topico_rel)
        .join(Item.tipo_rel)
        .join(Tipo.prioridad)
        .options(
            db.joinedload(Item.topico_rel),
            db.joinedload(Item.tipo_rel).joinedload(Tipo.prioridad),
            db.joinedload(Item.tags_asociados)
        )
        .offset(skip)
        .all()
    )
    return items

def get_item(db: Session, item_id: int):
    # join en cadena: Item → Topico, Tipo → Prioridad
    item = (
        db.query(Item)
        .filter(Item.id == item_id)
        .join(Item.topico_rel)
        .join(Item.tipo_rel)
        .join(Tipo.prioridad)
        .options(
            db.joinedload(Item.topico_rel),
            db.joinedload(Item.tipo_rel).joinedload(Tipo.prioridad),
            db.joinedload(Item.tags_asociados)
        )
        .first()
    )
    return item

def add_item(db: Session, item: Item):
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# delete all items by node_id
def delete_items_by_node_id(db: Session, node_id: str):
    db.query(Item).filter(Item.node_id == node_id).delete()
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

