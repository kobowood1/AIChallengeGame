import os
from app import create_app, socketio
import logging

logging.basicConfig(level=logging.DEBUG)

# Create the Flask application using the factory pattern with error handling
try:
    app = create_app()
except Exception as e:
    logging.error(f"Application startup error: {e}")
    app = Flask(__name__)
    @app.route('/')
    def error_page():
        return "Configuration error: Please check application logs"

if __name__ == "__main__":
    # Get port from environment variable for Replit compatibility
    port = int(os.environ.get("PORT", 5000))
    
    # Use eventlet as the async server for SocketIO
    socketio.run(app, host="0.0.0.0", port=port, debug=True, use_reloader=True, log_output=True)
