import os
import eventlet
# Patch standard library for use with eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
import logging
from flask_wtf.csrf import CSRFProtect

# Initialize SocketIO without an app instance yet
# Increased timeouts to prevent mid-deliberation disconnections
socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode='eventlet',
    ping_timeout=120,  # 2 minutes before considering client disconnected
    ping_interval=25,  # Send ping every 25 seconds to keep connection alive
    logger=False,      # Reduce log noise
    engineio_logger=False
)

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize login manager
login_manager = LoginManager()

def create_app():
    """
    Application factory function that creates and configures the Flask app
    """
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
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
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # User loader callback for Flask-Login - supports both User and Admin models
    @login_manager.user_loader
    def load_user(user_id):
        from models import User, Admin
        # Try to load as regular user first
        user = User.query.get(int(user_id))
        if user:
            return user
        # If not found, try admin user
        admin = Admin.query.get(int(user_id))
        return admin
    
    # Create all database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Register admin blueprint
    try:
        from admin_routes import admin as admin_blueprint
        app.register_blueprint(admin_blueprint)
        print("Admin blueprint registered successfully")
    except ImportError as e:
        print(f"Could not import admin routes: {e}")
    except Exception as e:
        print(f"Error registering admin blueprint: {e}")
    
    # Register multi-agent blueprint
    try:
        from routes_multi_agent import multi_agent_bp
        app.register_blueprint(multi_agent_bp)
        print("Multi-agent blueprint registered successfully")
    except ImportError as e:
        print(f"Could not import multi-agent routes: {e}")
    except Exception as e:
        print(f"Error registering multi-agent blueprint: {e}")
    
    # Import Socket.IO event handlers
    import events
    
    # Register new structured deliberation events
    from events_deliberation import register_deliberation_events
    register_deliberation_events(socketio)
    
    return app
