"""
Socket.IO event handlers for the AI challenge game
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio
from game import game_manager
import uuid
import logging

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logging.debug(f"Client connected: {request.sid}")
    emit('connected', {'client_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logging.debug(f"Client disconnected: {request.sid}")
    # Find and remove player from any games they're part of
    for game in game_manager.games.values():
        if request.sid in game.players:
            game.remove_player(request.sid)
            emit('player_left', {'player_id': request.sid}, room=game.room_id)
            # Update game state for remaining players
            emit('game_state_update', game.get_game_state(), room=game.room_id)

@socketio.on('create_game')
def handle_create_game(data):
    """
    Create a new game room
    
    Args:
        data: Dictionary containing:
            - username: Display name for the creator
    """
    username = data.get('username', 'Anonymous')
    room_id = str(uuid.uuid4())[:8]  # Generate a short unique room ID
    
    # Create the game
    game = game_manager.create_game(room_id)
    # Add the creator as a player
    game.add_player(request.sid, username)
    
    # Join the room
    join_room(room_id)
    
    logging.debug(f"Game created: {room_id} by {username}")
    
    # Send confirmation to the creator
    emit('game_created', {
        'room_id': room_id,
        'player_id': request.sid
    })
    
    # Broadcast game state
    emit('game_state_update', game.get_game_state(), room=room_id)

@socketio.on('join_game')
def handle_join_game(data):
    """
    Join an existing game room
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room to join
            - username: Display name for the player
    """
    room_id = data.get('room_id')
    username = data.get('username', 'Anonymous')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Game room not found'})
        return
    
    if game.state != 'waiting':
        emit('error', {'message': 'Game already started'})
        return
    
    # Add player to the game
    player = game.add_player(request.sid, username)
    
    # Join the room
    join_room(room_id)
    
    logging.debug(f"Player {username} joined game: {room_id}")
    
    # Notify the player
    emit('game_joined', {
        'room_id': room_id,
        'player_id': request.sid,
        'player': player
    })
    
    # Notify all players in the room
    emit('player_joined', {
        'player_id': request.sid,
        'username': username
    }, room=room_id)
    
    # Broadcast updated game state
    emit('game_state_update', game.get_game_state(), room=room_id)

@socketio.on('leave_game')
def handle_leave_game(data):
    """
    Leave a game room
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room to leave
    """
    room_id = data.get('room_id')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Game room not found'})
        return
    
    # Remove player from the game
    game.remove_player(request.sid)
    
    # Leave the room
    leave_room(room_id)
    
    logging.debug(f"Player {request.sid} left game: {room_id}")
    
    # Notify all players in the room
    emit('player_left', {'player_id': request.sid}, room=room_id)
    
    # Broadcast updated game state
    emit('game_state_update', game.get_game_state(), room=room_id)
    
    # If no players left, delete the game
    if len(game.players) == 0:
        game_manager.delete_game(room_id)

@socketio.on('start_game')
def handle_start_game(data):
    """
    Start a game
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room
    """
    room_id = data.get('room_id')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Game room not found'})
        return
    
    # Start the game
    challenge = game.start_game()
    
    if not challenge:
        emit('error', {'message': 'Could not start game'})
        return
    
    logging.debug(f"Game started: {room_id}")
    
    # Notify all players in the room
    emit('game_started', {
        'challenge': challenge,
        'state': game.get_game_state()
    }, room=room_id)

@socketio.on('submit_solution')
def handle_submit_solution(data):
    """
    Submit a solution for the current challenge
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room
            - solution: Code solution submitted
    """
    room_id = data.get('room_id')
    solution = data.get('solution')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Game room not found'})
        return
    
    # Submit the solution
    result = game.submit_solution(request.sid, solution)
    
    # Notify the submitting player
    emit('solution_submitted', result)
    
    # Broadcast updated game state
    emit('game_state_update', game.get_game_state(), room=room_id)
    
    # If game finished, notify everyone
    if game.state == 'finished':
        emit('game_finished', {
            'winners': game.winners,
            'state': game.get_game_state()
        }, room=room_id)

@socketio.on('get_game_state')
def handle_get_game_state(data):
    """
    Get the current state of a game
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room
    """
    room_id = data.get('room_id')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Game room not found'})
        return
    
    # Send the game state
    emit('game_state_update', game.get_game_state())
