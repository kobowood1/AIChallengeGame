import os
from flask import Flask
from flask_socketio import SocketIO
import logging

# Initialize SocketIO without an app instance yet
socketio = SocketIO()

def create_app():
    """
    Application factory function that creates and configures the Flask app
    """
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Initialize extensions with app
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Import Socket.IO event handlers
    import events
    
    return app
