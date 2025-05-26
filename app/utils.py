

def insertar_prioridades():
    from app import db 
    from app.database.models import Prioridad

    if Prioridad.query.count() == 0:
        print("⚙️ Insertando prioridades iniciales...")
        prioridades = [
            Prioridad(id=1, nombre="Muy baja", descripcion="Prioridad mínima", icono="bi-chevron-double-down"),
            Prioridad(id=2, nombre="Baja",     descripcion="Poca prioridad",   icono="bi-chevron-down"),
            Prioridad(id=3, nombre="Media",    descripcion="Prioridad media",  icono="bi-dash"),
            Prioridad(id=4, nombre="Alta",     descripcion="Alta prioridad",   icono="bi-chevron-up"),
            Prioridad(id=5, nombre="Urgente",  descripcion="Máxima prioridad", icono="bi-chevron-double-up"),
        ]
        db.session.bulk_save_objects(prioridades)
        db.session.commit()
        print("✅ Prioridades cargadas.")
    else:
        print("ℹ️ Las prioridades ya existen.")
