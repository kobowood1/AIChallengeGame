"""
Gunicorn configuration file for The CHALLENGE: Policy Jam - Refugee Edition application.
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
timeout = 120         # Increase worker timeout to 2 minutes
keepalive = 120        # Keep connections alive for 2 minutes

# Worker settings
workers = 1
threads = 4