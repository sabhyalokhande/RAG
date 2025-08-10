from quart import Quart
from quart_cors import cors
from app.routes.rag_routes import rag_routes

def create_app():
    app = Quart(__name__)
    app = cors(app)
    
    # Register blueprints
    app.register_blueprint(rag_routes)
    
    return app