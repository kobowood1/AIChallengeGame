"""
Socket.IO event handlers for the AI policy deliberation simulation
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio
from game import game_manager
import uuid
import logging
import random
import time

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

@socketio.on('create_deliberation')
def handle_create_deliberation(data):
    """
    Create a new policy deliberation room
    
    Args:
        data: Dictionary containing:
            - username: Display name for the policy advisor creating the room
    """
    username = data.get('username', 'Anonymous')
    room_id = str(uuid.uuid4())[:8]  # Generate a short unique room ID
    
    # Create the game
    game = game_manager.create_game(room_id)
    # Add the creator as a player
    game.add_player(request.sid, username)
    
    # Join the room
    join_room(room_id)
    
    logging.debug(f"Policy deliberation room created: {room_id} by {username}")
    
    # Send confirmation to the creator
    emit('deliberation_created', {
        'room_id': room_id,
        'advisor_id': request.sid
    })
    
    # Broadcast game state
    emit('game_state_update', game.get_game_state(), room=room_id)

@socketio.on('join_deliberation')
def handle_join_deliberation(data):
    """
    Join an existing policy deliberation room
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the deliberation room to join
            - username: Display name for the policy advisor
    """
    room_id = data.get('room_id')
    username = data.get('username', 'Anonymous')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Policy deliberation room not found'})
        return
    
    if game.state != 'waiting':
        emit('error', {'message': 'Policy deliberation already in progress'})
        return
    
    # Add player to the game
    player = game.add_player(request.sid, username)
    
    # Join the room
    join_room(room_id)
    
    logging.debug(f"Policy advisor {username} joined deliberation room: {room_id}")
    
    # Add AI agents as players if this is a human player joining
    from ai_agents import generate_agents
    
    # First check if there are already AI agents in the game (by checking for names that start with "AI-")
    ai_agents_exist = any(p.get('username', '').startswith('AI-') for p in game.players.values())
    
    if not ai_agents_exist:
        # Generate 4 AI agents
        agents = generate_agents()
        
        # Add them to the game
        for i, agent in enumerate(agents):
            ai_player_id = f"ai-agent-{i}-{room_id}"
            ai_username = f"AI-{agent['name']}"
            
            # Add AI player to game
            game.add_player(ai_player_id, ai_username)
            
            # Notify all advisors about the new AI agent
            emit('advisor_joined', {
                'advisor_id': ai_player_id,
                'username': ai_username
            }, room=room_id)
    
    # Notify the policy advisor
    emit('deliberation_joined', {
        'room_id': room_id,
        'advisor_id': request.sid,
        'advisor': player
    })
    
    # Notify all advisors in the room about the human advisor
    emit('advisor_joined', {
        'advisor_id': request.sid,
        'username': username
    }, room=room_id)
    
    # Broadcast updated game state
    emit('game_state_update', game.get_game_state(), room=room_id)

@socketio.on('leave_deliberation')
def handle_leave_deliberation(data):
    """
    Leave a policy deliberation room
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the deliberation room to leave
    """
    room_id = data.get('room_id')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Policy deliberation room not found'})
        return
    
    # Remove player from the game
    game.remove_player(request.sid)
    
    # Leave the room
    leave_room(room_id)
    
    logging.debug(f"Policy advisor {request.sid} left deliberation room: {room_id}")
    
    # Notify all advisors in the room
    emit('advisor_left', {'advisor_id': request.sid}, room=room_id)
    
    # Broadcast updated game state
    emit('game_state_update', game.get_game_state(), room=room_id)
    
    # If no players left, delete the game
    if len(game.players) == 0:
        game_manager.delete_game(room_id)

@socketio.on('start_deliberation')
def handle_start_deliberation(data):
    """
    Begin the policy deliberation session
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room
    """
    room_id = data.get('room_id')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Policy deliberation room not found'})
        return
    
    # Start the policy deliberation session
    challenge = game.start_game()
    
    if not challenge:
        emit('error', {'message': 'Could not start policy deliberation'})
        return
    
    logging.debug(f"Policy deliberation started: {room_id}")
    
    # Notify all policy advisors in the room
    emit('deliberation_started', {
        'challenge': challenge,
        'state': game.get_game_state()
    }, room=room_id)

@socketio.on('submit_policy_proposal')
def handle_submit_policy_proposal(data):
    """
    Submit a policy proposal for the current challenge
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room
            - solution: Policy proposal text submitted
    """
    room_id = data.get('room_id')
    solution = data.get('solution')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Policy deliberation room not found'})
        return
    
    # Submit the policy proposal
    result = game.submit_solution(request.sid, solution)
    
    # Notify the submitting player
    emit('policy_proposal_submitted', result)
    
    # Broadcast updated game state
    emit('game_state_update', game.get_game_state(), room=room_id)
    
    # If policy deliberation finished, notify everyone
    if game.state == 'finished':
        emit('deliberation_finished', {
            'winners': game.winners,
            'state': game.get_game_state()
        }, room=room_id)

@socketio.on('get_deliberation_state')
def handle_get_deliberation_state(data):
    """
    Get the current state of a policy deliberation session
    
    Args:
        data: Dictionary containing:
            - room_id: ID of the room
    """
    room_id = data.get('room_id')
    
    # Get the game
    game = game_manager.get_game(room_id)
    
    if not game:
        emit('error', {'message': 'Policy deliberation room not found'})
        return
    
    # Send the game state
    emit('game_state_update', game.get_game_state())

# Policy Discussion and Voting Events

@socketio.on('join_policy_room')
def handle_join_policy_room(data):
    """
    Join a policy discussion room
    
    Args:
        data: Dictionary containing:
            - room_id: Unique room identifier for the discussion (usually the session ID)
    """
    from flask import session
    import time
    from ai_agents import agent_justify
    
    room_id = data.get('room_id')
    
    if not room_id:
        emit('error', {'message': 'Room ID required'})
        return
    
    join_room(room_id)
    
    # Store room in session
    session['policy_room'] = room_id
    
    # Get the agents and player selections from the session
    agents = session.get('agents', [])
    selections = session.get('player_package', {})
    
    if not agents or not selections:
        emit('error', {'message': 'Session data missing'})
        return
    
    # Send welcome message
    emit('chat_message', {
        'sender': 'System',
        'message': 'Welcome to the policy discussion. Agents will now share their thoughts.',
        'timestamp': time.time()
    }, to=room_id)
    
    # Let each agent post their initial justifications
    for policy_name, option_level in selections.items():
        # Add a small delay to make messages appear naturally (but not too long)
        time.sleep(0.3)
        
        for agent in agents:
            justification = agent_justify(policy_name, option_level, agent)
            
            emit('chat_message', {
                'sender': agent['name'],
                'message': f"On {policy_name} (Option {option_level}): {justification}",
                'agent': agent,
                'timestamp': time.time(),
                'policy': policy_name
            }, to=room_id)

@socketio.on('send_message')
def handle_send_message(data):
    """
    Send a message in the policy discussion
    
    Args:
        data: Dictionary containing:
            - message: The message content
            - sender: Name of the sender (default: 'You')
            - policy_name: Optional policy being discussed
    """
    from flask import session
    import time
    
    room_id = session.get('policy_room')
    if not room_id:
        emit('error', {'message': 'Not in a discussion room'})
        return
    
    message = data.get('message')
    sender = data.get('sender', 'You')
    policy_name = data.get('policy_name', None)
    
    if not message:
        return
    
    # Store message in conversation history
    conversation_history = session.get('conversation_history', [])
    
    # Limit history size
    if len(conversation_history) >= 20:
        conversation_history = conversation_history[1:]  # Remove oldest message
    
    # Add new message to history
    conversation_history.append({
        'sender': sender,
        'message': message,
        'timestamp': time.time(),
        'is_player': True,
        'policy': policy_name
    })
    
    # Update session
    session['conversation_history'] = conversation_history
    
    # Store the latest user message separately for AI context
    session['latest_user_message'] = message
    
    # Broadcast the message to the room
    emit('chat_message', {
        'sender': sender,
        'message': message,
        'timestamp': time.time(),
        'is_player': True,
        'policy': policy_name
    }, to=room_id)

@socketio.on('update_conversation_history')
def handle_update_conversation_history(data):
    """
    Update the conversation history with a new message (used by background tasks)
    
    Args:
        data: Dictionary containing:
            - sender: Name of the message sender
            - message: The message content
            - policy_name: Optional policy being discussed
    """
    from flask import session
    import time
    
    room_id = session.get('policy_room')
    if not room_id:
        return
    
    sender = data.get('sender')
    message = data.get('message')
    policy_name = data.get('policy')
    
    if not sender or not message:
        return
    
    # Get conversation history
    conversation_history = session.get('conversation_history', [])
    
    # Limit history size
    if len(conversation_history) >= 20:
        conversation_history = conversation_history[1:]  # Remove oldest message
    
    # Add new message to history
    conversation_history.append({
        'sender': sender,
        'message': message,
        'timestamp': time.time(),
        'policy': policy_name
    })
    
    # Update session
    session['conversation_history'] = conversation_history

@socketio.on('agent_response')
def handle_agent_response(data):
    """
    Trigger an agent to respond to a player message, considering recent conversation context
    
    Args:
        data: Dictionary containing:
            - agent_index: Index of the agent to respond
            - policy_name: The policy being discussed
            - user_message: The most recent message from the user (optional)
    """
    from flask import session
    import time
    from ai_agents import agent_justify
    
    room_id = session.get('policy_room')
    if not room_id:
        emit('error', {'message': 'Not in a discussion room'})
        return
    
    agent_index = data.get('agent_index')
    policy_name = data.get('policy_name')
    user_message = data.get('user_message', '')
    
    # Get conversation history from session if available
    conversation_history = session.get('conversation_history', [])
    
    # Limit to last 5 messages to keep the context relevant
    recent_messages = conversation_history[-5:] if conversation_history else []
    
    agents = session.get('agents', [])
    selections = session.get('player_package', {})
    
    if not agents or agent_index is None or agent_index >= len(agents):
        return
    
    agent = agents[agent_index]
    
    # Generate a response that addresses the player's point
    try:
        # Use the policy's option level from the player's selections
        option_level = selections.get(policy_name, 2)  # Default to option 2 if not found
        
        # Generate a justification as a response, including conversation context
        justification = agent_justify(policy_name, option_level, agent, user_message, recent_messages)
        
        # Store this message in the conversation history
        if len(conversation_history) >= 20:  # Limit history to prevent session from getting too large
            conversation_history = conversation_history[1:]  # Remove oldest message
            
        conversation_history.append({
            'sender': agent['name'],
            'message': justification,
            'timestamp': time.time(),
            'policy': policy_name
        })
        
        # Update session
        session['conversation_history'] = conversation_history
        
        emit('chat_message', {
            'sender': agent['name'],
            'message': justification,
            'agent': agent,
            'timestamp': time.time(),
            'policy': policy_name
        }, to=room_id)
        
        # 25% chance for spontaneous debate between two random agents about this policy
        if random.random() < 0.25:
            # Schedule a follow-up debate between two random agents
            socketio.start_background_task(
                generate_agent_debate, 
                room_id, 
                agent, 
                policy_name, 
                option_level, 
                agents, 
                conversation_history
            )
            
    except Exception as e:
        logging.error(f"Error generating agent response: {e}")

def generate_agent_debate(room_id, first_agent, policy_name, option_level, agents, conversation_history):
    """
    Generate a spontaneous debate between two AI agents about a policy area
    
    Args:
        room_id: The room ID for emitting messages
        first_agent: The agent who just spoke
        policy_name: The policy being discussed
        option_level: The first agent's option level for this policy
        agents: List of all available agents
        conversation_history: Recent conversation history
    """
    from ai_agents import agent_justify
    import time
    
    # Don't debate if we have fewer than 2 agents
    if len(agents) < 2:
        return
    
    try:
        # Get available agents (excluding first_agent)
        available_agents = [a for a in agents if a['name'] != first_agent['name']]
        
        # Select a random agent to debate with the first agent
        second_agent = random.choice(available_agents)
        
        # Determine a policy position (may be different from first agent's)
        # Agents with different ideologies might prefer different options
        ideology_option_preferences = {
            "conservative": [1, 2],  # Conservative agents prefer lower-cost options
            "moderate": [2, 1, 3],   # Moderate agents prefer middle-ground
            "liberal": [2, 3],       # Liberal agents prefer moderate to comprehensive options
            "socialist": [3, 2],     # Socialist agents prefer comprehensive options
            "neoliberal": [1, 2]     # Neoliberal agents prefer market-based solutions (lower options)
        }
        
        # Get preference list based on ideology, defaulting to all options if not found
        preference_list = ideology_option_preferences.get(
            second_agent.get('ideology', ''), 
            [1, 2, 3]
        )
        
        # Choose an option level with 60% chance of being different from first_agent's
        if random.random() < 0.6 and len(preference_list) > 1:
            # Filter out the first agent's option if possible
            filtered_preferences = [p for p in preference_list if p != option_level]
            if filtered_preferences:
                second_option = random.choice(filtered_preferences)
            else:
                second_option = random.choice(preference_list)
        else:
            second_option = random.choice(preference_list)
        
        # Introduce a small delay to make the conversation feel natural
        time.sleep(1.5)
        
        # Create a prompt specifically for continuing the conversation
        second_agent_message = f"I've been listening to {first_agent['name']}'s perspective on {policy_name}..."
        
        # Generate a response from the second agent that references the first agent's position
        second_response = agent_justify(
            policy_name, 
            second_option, 
            second_agent, 
            first_agent['name'] + ' said: ' + conversation_history[-1]['message'],
            conversation_history[-5:] if conversation_history else []
        )
        
        # Emit the response to the room
        socketio.emit('chat_message', {
            'sender': second_agent['name'],
            'message': second_response,
            'agent': second_agent,
            'timestamp': time.time(),
            'policy': policy_name
        }, to=room_id)
        
        # Add to conversation history (needs to be done through socket event for thread safety)
        socketio.emit('update_conversation_history', {
            'sender': second_agent['name'],
            'message': second_response,
            'policy': policy_name
        }, to=room_id)
        
    except Exception as e:
        logging.error(f"Error generating agent debate: {e}")

@socketio.on('call_vote')
def handle_call_vote(data):
    """
    Trigger the final voting process
    
    Args:
        data: Dictionary containing no specific parameters
    """
    from flask import session
    import time
    import random
    from game_data import POLICIES, validate_package, MAX_BUDGET
    
    room_id = session.get('policy_room')
    if not room_id:
        emit('error', {'message': 'Not in a discussion room'})
        return
    
    agents = session.get('agents', [])
    player_selections = session.get('player_package', {})
    
    if not agents or not player_selections:
        emit('error', {'message': 'Session data missing'})
        return
    
    # Announce the start of voting
    emit('chat_message', {
        'sender': 'System',
        'message': 'Voting has started. Agents are submitting their final choices...',
        'timestamp': time.time()
    }, to=room_id)
    
    time.sleep(1)
    
    # Track votes for each policy
    policy_votes = {}
    for policy in POLICIES:
        policy_name = policy['name']
        policy_votes[policy_name] = {1: 0, 2: 0, 3: 0}
    
    # Have each agent vote
    for agent in agents:
        # Add a small delay for realism
        time.sleep(0.5)
        
        agent_votes = {}
        
        # For each policy, the agent casts a vote
        for policy in POLICIES:
            policy_name = policy['name']
            
            # In a real implementation, this would be more sophisticated and based on the discussion
            # For now, we'll randomly lean toward the player's choice or slightly modify it
            player_choice = player_selections.get(policy_name, 2)
            
            # 50% chance to agree with player, 25% to go one level up, 25% to go one level down
            vote_modifier = random.choices([-1, 0, 0, 1], [0.25, 0.25, 0.25, 0.25])[0]
            agent_vote = max(1, min(3, player_choice + vote_modifier))
            
            # Record the vote
            policy_votes[policy_name][agent_vote] += 1
            agent_votes[policy_name] = agent_vote
            
            # Announce the agent's vote
            emit('chat_message', {
                'sender': agent['name'],
                'message': f"I vote for Option {agent_vote} on {policy_name}.",
                'agent': agent,
                'timestamp': time.time(),
                'is_vote': True,
                'policy': policy_name,
                'vote': agent_vote
            }, to=room_id)
        
        # Store the agent's votes in the session for display
        if 'agent_votes' not in session:
            session['agent_votes'] = {}
        
        session['agent_votes'][agent['name']] = agent_votes
    
    # Determine the winning option for each policy
    final_package = {}
    for policy_name, votes in policy_votes.items():
        # Find the option with the most votes
        max_votes = 0
        winning_options = []
        
        for option, vote_count in votes.items():
            if vote_count > max_votes:
                max_votes = vote_count
                winning_options = [option]
            elif vote_count == max_votes:
                winning_options.append(option)
        
        # Break ties randomly
        final_package[policy_name] = random.choice(winning_options)
    
    # Validate the package against budget constraints
    is_valid, total_cost, error_message = validate_package(final_package)
    
    # If over budget, reduce costs by downgrading the most expensive policies
    while not is_valid and 'over budget' in error_message.lower():
        # Find policy costs
        policy_costs = {}
        for policy_name, option_level in final_package.items():
            for policy in POLICIES:
                if policy['name'] == policy_name:
                    policy_costs[policy_name] = policy['options'][option_level - 1]['cost']
                    break
        
        # Find the most expensive policy that can be downgraded
        most_expensive = None
        highest_cost = 0
        
        for policy_name, cost in policy_costs.items():
            current_level = final_package[policy_name]
            if cost > highest_cost and current_level > 1:
                highest_cost = cost
                most_expensive = policy_name
        
        if most_expensive:
            # Downgrade the policy
            final_package[most_expensive] -= 1
            
            # Announce the change
            emit('chat_message', {
                'sender': 'System',
                'message': f"Budget exceeded. Downgrading {most_expensive} to Option {final_package[most_expensive]} to stay within budget.",
                'timestamp': time.time()
            }, to=room_id)
            
            # Revalidate
            is_valid, total_cost, error_message = validate_package(final_package)
        else:
            # If we can't downgrade any more, we're stuck
            break
    
    # Store the final package in the session
    session['final_package'] = final_package
    session['final_cost'] = total_cost
    
    # Announce the final package
    emit('chat_message', {
        'sender': 'System',
        'message': f"Voting complete. Final budget: {total_cost} / {MAX_BUDGET}",
        'timestamp': time.time(),
        'is_final': True
    }, to=room_id)
    
    # Send the final package details
    emit('voting_complete', {
        'final_package': final_package,
        'total_cost': total_cost,
        'is_valid': is_valid
    }, to=room_id)
