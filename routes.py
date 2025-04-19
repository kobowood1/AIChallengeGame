from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Route for the home page"""
    return render_template('index.html')

@main.route('/game')
def game():
    """Route for the game page"""
    return render_template('game.html')