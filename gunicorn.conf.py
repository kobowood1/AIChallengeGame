"""
Gunicorn configuration file for the AI Challenge Game application.
"""
# Use eventlet worker for WebSocket support
worker_class = 'eventlet'

# Bind to all interfaces
bind = '0.0.0.0:5000'

# Enable auto-reload for development
reload = True

# Set logging level
loglevel = 'info'

# Timeout settings for long-polling
timeout = 60
keepalive = 60

# Worker settings
workers = 1
threads = 4