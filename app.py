import os
import eventlet
# Patch standard library for use with eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
import logging
from flask_wtf.csrf import CSRFProtect

# Initialize SocketIO without an app instance yet
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# Initialize CSRF protection
csrf = CSRFProtect()

def create_app():
    """
    Application factory function that creates and configures the Flask app
    """
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Set debug mode explicitly
    app.config['DEBUG'] = True
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Initialize extensions with app
    socketio.init_app(app)
    csrf.init_app(app)
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Create all database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Import Socket.IO event handlers
    import events
    
    return app
