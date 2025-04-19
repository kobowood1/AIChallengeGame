from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class Participant(db.Model):
    """Model for storing participant information"""
    id = db.Column(db.Integer, primary_key=True)
    
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