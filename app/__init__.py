from flask import Flask
from flask_cors import CORS
from app.routes.rag_routes import rag_routes

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(rag_routes)
    
    return app