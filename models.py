from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Model for user authentication and management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    
    # Account management
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    @property
    def is_active(self):
        """Required by Flask-Login"""
        return self.active
    
    # Relationships
    participants = db.relationship('Participant', backref='user', lazy=True)
    game_sessions = db.relationship('GameSession', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'


class GameSession(db.Model):
    """Model for tracking user game sessions and progress"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    
    # Game progress
    current_phase = db.Column(db.String(20), default='registration')  # registration, scenario, phase1, phase2, phase3, completed
    policy_selections = db.Column(db.Text, nullable=True)  # JSON string of selections
    ai_agents = db.Column(db.Text, nullable=True)  # JSON string of generated agents
    conversation_history = db.Column(db.Text, nullable=True)  # JSON string of chat messages
    final_package = db.Column(db.Text, nullable=True)  # JSON string of final voted package
    reflection_responses = db.Column(db.Text, nullable=True)  # JSON string of reflection answers
    
    # Session metadata
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(32)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self):
        return f'<GameSession {self.id} for User {self.user_id}>'


class Participant(db.Model):
    """Model for storing participant information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Link to authenticated user
    
    # Personal information
    age = db.Column(db.Integer, nullable=False)
    nationality = db.Column(db.String(100), nullable=False)
    occupation = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(100), nullable=False)
    displacement_experience = db.Column(db.Text, nullable=True)
    current_location_city = db.Column(db.String(100), nullable=False)
    current_location_country = db.Column(db.String(100), nullable=False)
    
    # Session information
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Participant {self.id} from {self.current_location_city}, {self.current_location_country}>'