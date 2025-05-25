from .main import main
from .topic import topic
from .type import type_route
from .opc_routes import opc_route

def register_routes(app):
    app.register_blueprint(main)
    app.register_blueprint(topic)
    app.register_blueprint(type_route)
    app.register_blueprint(opc_route)
