"""
Forms for user authentication and registration
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, ValidationError
from models import User


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or log in.')


class ParticipantForm(FlaskForm):
    """Participant demographic information form"""
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=13, max=120)])
    nationality = StringField('Nationality', validators=[DataRequired(), Length(max=100)])
    occupation = StringField('Occupation', validators=[DataRequired(), Length(max=100)])
    education_level = SelectField('Education Level', 
                                 choices=[
                                     ('Primary/Elementary School', 'Primary/Elementary School'),
                                     ('Secondary/High School', 'Secondary/High School'),
                                     ('Some College/University', 'Some College/University'),
                                     ('Bachelor\'s Degree', 'Bachelor\'s Degree'),
                                     ('Master\'s Degree', 'Master\'s Degree'),
                                     ('Doctoral Degree', 'Doctoral Degree'),
                                     ('Professional Degree', 'Professional Degree'),
                                     ('Other', 'Other')
                                 ],
                                 validators=[DataRequired()])
    displacement_experience = TextAreaField('Have you or your family experienced displacement? (Optional)', 
                                          validators=[Length(max=500)])
    current_location_city = StringField('Current City', validators=[DataRequired(), Length(max=100)])
    current_location_country = StringField('Current Country', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Continue to Scenario')