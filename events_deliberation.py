"""
Socket.IO event handlers for structured multi-agent policy deliberation
"""
import time
import logging
from flask import session, request
from flask_socketio import emit, join_room, leave_room
from multi_agent_system import MultiAgentSimulation
from challenge_content import POLICY_AREAS

# Global socketio instance will be set when registering events
socketio = None

# Deliberation state management
deliberation_sessions = {}

class DeliberationSession:
    """Manages the state of a structured policy deliberation session"""
    
    def __init__(self, session_id, user_name, agent_names, user_policy, agent_policies):
        self.session_id = session_id
        self.user_name = user_name
        self.agent_names = agent_names
        self.user_policy = user_policy
        self.agent_policies = agent_policies
        self.current_step = 0
        self.current_policy_index = 0
        self.votes = {}
        self.final_package = {}
        self.simulation = MultiAgentSimulation(agent_names)
        self.conversation_history = []
        
        # Steps in the deliberation process
        self.steps = [
            'moderator_intro',
            'agent_introductions', 
            'user_introduction',
            'policy_deliberation',
            'final_recommendations'
        ]
        
    def get_current_step(self):
        """Get the current step name"""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return 'complete'
    
    def advance_step(self):
        """Move to the next step"""
        self.current_step += 1
        
    def get_policy_area(self, index):
        """Get policy area by index"""
        if 0 <= index < len(POLICY_AREAS):
            return POLICY_AREAS[index]
        return None
    
    def get_user_choice(self, policy_name):
        """Get user's choice for a policy area"""
        return self.user_policy.get(policy_name, 1)
    
    def get_agent_choice(self, agent_name, policy_name):
        """Get agent's choice for a policy area"""
        return self.agent_policies.get(agent_name, {}).get(policy_name, 1)
    
    def add_vote(self, voter, option):
        """Add a vote for the current policy"""
        policy_name = self.get_policy_area(self.current_policy_index).name
        if policy_name not in self.votes:
            self.votes[policy_name] = {}
        self.votes[policy_name][voter] = option
    
    def get_votes(self, policy_name):
        """Get all votes for a policy area"""
        return self.votes.get(policy_name, {})
    
    def calculate_majority(self, policy_name):
        """Calculate majority vote for a policy area"""
        votes = self.get_votes(policy_name)
        if not votes:
            return 1  # Default to option 1
        
        # Count votes
        vote_counts = {}
        for vote in votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        # Find majority
        max_count = max(vote_counts.values())
        winners = [option for option, count in vote_counts.items() if count == max_count]
        
        # Random tie-breaking
        import random
        return random.choice(winners)

def register_deliberation_events(socketio_instance):
    """Register all deliberation-related Socket.IO events"""
    global socketio
    socketio = socketio_instance
    
    @socketio_instance.on('join_deliberation_room')
    def handle_join_deliberation_room():
        """Initialize and join the structured deliberation session"""
        session_id = request.sid
        join_room(session_id)
        
        # Get session data
        user_name = session.get('user_name', 'Participant')
        agent_names = session.get('agent_names', ['Agent1', 'Agent2', 'Agent3', 'Agent4'])
        user_policy = session.get('policy_selections', {})
        agent_policies = session.get('agent_policies', {})
        
        # Create deliberation session
        delib_session = DeliberationSession(
            session_id, user_name, agent_names, user_policy, agent_policies
        )
        deliberation_sessions[session_id] = delib_session
        
        logging.info(f"Started deliberation session for {user_name}")
        
        # Start with moderator introduction
        start_moderator_intro(session_id)

def start_moderator_intro(session_id):
    """Step 1: Moderator introduces the session"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    agent_list = ', '.join(delib_session.agent_names[:-1]) + f", and {delib_session.agent_names[-1]}"
    
    intro_message = (
        f"Welcome to the Republic of Bean policy simulation. Today we will review "
        f"how your choices impact refugee education, social cohesion, and resources. "
        f"We have four stakeholders ({agent_list}) plus you, {delib_session.user_name}. "
        f"Let us begin with introductions."
    )
    
    emit('moderator_message', {
        'message': intro_message,
        'step': 1,
        'progress': 'Step 1: Welcome & Introduction'
    }, room=session_id)
    
    # Advance to agent introductions after a short delay
    socketio.sleep(2)
    start_agent_introductions(session_id)

def start_agent_introductions(session_id):
    """Step 2: Agents introduce themselves sequentially"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    delib_session.advance_step()
    
    emit('moderator_message', {
        'message': "Let's have our expert panel introduce themselves.",
        'step': 2,
        'progress': 'Step 2: Expert Introductions'
    }, room=session_id)
    
    # Generate agent introductions sequentially
    for i, agent_name in enumerate(delib_session.agent_names):
        socketio.sleep(1)  # Natural delay between introductions
        
        # Generate agent profile intro
        agent_profile = delib_session.simulation.agents[agent_name]
        age = 35 + (i * 5)  # Simple age assignment
        
        # Get agent's policy summary
        policy_summary = generate_policy_summary(agent_name, delib_session.agent_policies.get(agent_name, {}))
        
        intro_text = (
            f"Hello! I'm {agent_name}, {age}, {agent_profile.background}. "
            f"My policy approach focuses on {policy_summary}."
        )
        
        emit('agent_message', {
            'sender': agent_name,
            'message': intro_text,
            'agentType': agent_profile.model_type
        }, room=session_id)
    
    # Move to user introduction
    socketio.sleep(2)
    start_user_introduction(session_id)

def generate_policy_summary(agent_name, agent_policy):
    """Generate a brief summary of agent's policy choices"""
    if not agent_policy:
        return "comprehensive and balanced solutions"
    
    # Count option levels
    option_counts = {}
    for policy_name, level in agent_policy.items():
        option_counts[level] = option_counts.get(level, 0) + 1
    
    # Generate summary based on predominant choices
    if option_counts.get(3, 0) > option_counts.get(1, 0):
        return "comprehensive, well-funded programs"
    elif option_counts.get(1, 0) > option_counts.get(3, 0):
        return "cost-effective, targeted interventions"
    else:
        return "balanced, pragmatic approaches"

def start_user_introduction(session_id):
    """Step 3: Ask user to introduce themselves"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    delib_session.advance_step()
    
    emit('moderator_message', {
        'message': f"Now, {delib_session.user_name}, please introduce yourself — your background and what guided your policy choices.",
        'step': 3,
        'progress': 'Step 3: Your Introduction',
        'enableInput': True
    }, room=session_id)

def start_policy_deliberation(session_id):
    """Step 4: Begin policy-by-policy deliberation"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    delib_session.advance_step()
    delib_session.current_policy_index = 0
    
    emit('moderator_message', {
        'message': "Thank you. Now let's discuss each policy area systematically.",
        'step': 4,
        'progress': 'Step 4: Policy Deliberation'
    }, room=session_id)
    
    # Start with first policy area
    socketio.sleep(1)
    discuss_policy_area(session_id, 0)

def discuss_policy_area(session_id, policy_index):
    """Discuss a specific policy area"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    if policy_index >= len(POLICY_AREAS):
        # All policies discussed, move to final recommendations
        start_final_recommendations(session_id)
        return
    
    policy_area = POLICY_AREAS[policy_index]
    delib_session.current_policy_index = policy_index
    
    emit('moderator_message', {
        'message': f"Policy #{policy_index + 1}: {policy_area.name}. Agents, please state your chosen option and rationale.",
        'step': 4,
        'progress': f'Policy {policy_index + 1}/7: {policy_area.name}',
        'policyIndex': policy_index
    }, room=session_id)
    
    # Get agent responses
    socketio.sleep(1)
    get_agent_policy_responses(session_id, policy_area)

def get_agent_policy_responses(session_id, policy_area):
    """Get each agent's policy choice and rationale"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    agent_choices = {}
    
    for agent_name in delib_session.agent_names:
        socketio.sleep(1)  # Natural delay
        
        agent_choice = delib_session.get_agent_choice(agent_name, policy_area.name)
        agent_choices[agent_name] = agent_choice
        
        # Generate rationale using AI
        agent_profile = delib_session.simulation.agents[agent_name]
        
        # Create a simple context for the rationale
        context = f"Policy area: {policy_area.name}\nYour choice: Option {agent_choice}\nBriefly explain your rationale in 1-2 sentences."
        
        try:
            # Set the policy context for the agent
            delib_session.simulation.set_policy_context(policy_area.name, {}, agent_choice)
            rationale = delib_session.simulation.generate_agent_response(agent_name, context)
            response_text = f"I selected Option {agent_choice}. {rationale}"
        except Exception as e:
            logging.error(f"Error generating agent response for {agent_name}: {e}")
            # Use fallback based on agent profile
            if 'cost-effective' in agent_profile.ideology.lower():
                response_text = f"I selected Option {agent_choice} because it provides a cost-effective approach that fits our budget constraints."
            elif 'comprehensive' in agent_profile.ideology.lower():
                response_text = f"I selected Option {agent_choice} because it offers comprehensive support for refugee students."
            else:
                response_text = f"I selected Option {agent_choice} based on my experience and the needs of refugee students."
        
        agent_profile = delib_session.simulation.agents[agent_name]
        emit('agent_message', {
            'sender': agent_name,
            'message': response_text,
            'agentType': agent_profile.model_type
        }, room=session_id)
    
    # Ask user for their choice
    socketio.sleep(2)
    ask_user_policy_choice(session_id, policy_area, agent_choices)

def ask_user_policy_choice(session_id, policy_area, agent_choices):
    """Ask user to explain their policy choice"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    user_choice = delib_session.get_user_choice(policy_area.name)
    
    emit('moderator_message', {
        'message': f"{delib_session.user_name}, why did you choose Option {user_choice}?",
        'enableInput': True,
        'policyIndex': delib_session.current_policy_index
    }, room=session_id)
    
    # Check if voting is needed
    all_choices = list(agent_choices.values()) + [user_choice]
    unique_choices = set(all_choices)
    
    if len(unique_choices) == 1:
        # Everyone agreed
        agreed_option = list(unique_choices)[0]
        delib_session.final_package[policy_area.name] = agreed_option
        
        # Continue to next policy after user explains
        # (handled in user_message event)
    else:
        # Voting will be needed after user explains
        pass

def start_voting(session_id, policy_area):
    """Start voting process for a policy area"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    emit('start_voting', {
        'message': f"We have different perspectives on {policy_area.name}. Please vote by selecting your preferred option.",
        'policyArea': policy_area.name
    }, room=session_id)
    
    # Collect agent votes
    for agent_name in delib_session.agent_names:
        agent_choice = delib_session.get_agent_choice(agent_name, policy_area.name)
        delib_session.add_vote(agent_name, agent_choice)
    
    # Wait for user vote (handled in cast_vote event)

def start_final_recommendations(session_id):
    """Step 5: Present final recommendations"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    delib_session.advance_step()
    
    # Generate final package summary
    package_summary = []
    for policy_area in POLICY_AREAS:
        option = delib_session.final_package.get(policy_area.name, 1)
        package_summary.append(f"{policy_area.name}: Option {option}")
    
    final_message = (
        f"Final group policy package:\n" +
        "\n".join(package_summary) + 
        "\n\nCongratulations on completing this policy deliberation!"
    )
    
    emit('deliberation_complete', {
        'message': final_message,
        'finalPackage': delib_session.final_package
    }, room=session_id)
    
    # Store final package in session
    session['final_package'] = delib_session.final_package

    @socketio_instance.on('user_message')
    def handle_user_message(data):
        """Handle user messages during deliberation"""
        session_id = request.sid
        delib_session = deliberation_sessions.get(session_id)
        if not delib_session:
            return
        
        message = data.get('message', '')
        step = data.get('step', 0)
        policy_index = data.get('policyIndex', 0)
        
        # Record message in conversation history
        delib_session.conversation_history.append({
            'sender': delib_session.user_name,
            'message': message,
            'timestamp': time.time()
        })
        
        current_step = delib_session.get_current_step()
        
        if current_step == 'user_introduction':
            # User has introduced themselves, move to policy deliberation
            try:
                socketio.sleep(1)
                start_policy_deliberation(session_id)
            except Exception as e:
                logging.error(f"Error starting policy deliberation: {e}")
                emit('system_message', {
                    'message': f"Error starting policy deliberation: {str(e)}. Please refresh the page."
                }, room=session_id)
            
        elif current_step == 'policy_deliberation':
            # User explained their choice, check if we need voting
            policy_area = delib_session.get_policy_area(policy_index)
            if not policy_area:
                return
            
            # Get all choices for this policy
            user_choice = delib_session.get_user_choice(policy_area.name)
            agent_choices = {}
            for agent_name in delib_session.agent_names:
                agent_choices[agent_name] = delib_session.get_agent_choice(agent_name, policy_area.name)
            
            all_choices = list(agent_choices.values()) + [user_choice]
            unique_choices = set(all_choices)
            
            if len(unique_choices) == 1:
                # Everyone agreed
                agreed_option = list(unique_choices)[0]
                delib_session.final_package[policy_area.name] = agreed_option
                
                emit('moderator_message', {
                    'message': f"All agreed on Option {agreed_option}. Moving on.",
                    'step': 4
                }, room=session_id)
                
                # Move to next policy
                socketio.sleep(2)
                discuss_policy_area(session_id, policy_index + 1)
            else:
                # Need voting
                socketio.sleep(1)
                start_voting(session_id, policy_area)

    @socketio_instance.on('cast_vote')
    def handle_cast_vote(data):
        """Handle user vote during policy deliberation"""
        session_id = request.sid
        delib_session = deliberation_sessions.get(session_id)
        if not delib_session:
            return
        
        option = data.get('option', 1)
        policy_index = data.get('policyIndex', 0)
        
        policy_area = delib_session.get_policy_area(policy_index)
        if not policy_area:
            return
        
        # Add user vote
        delib_session.add_vote(delib_session.user_name, option)
        
        # Calculate majority
        majority_option = delib_session.calculate_majority(policy_area.name)
        delib_session.final_package[policy_area.name] = majority_option
        
        emit('vote_result', {
            'message': f"Majority selected Option {majority_option}.",
            'policyArea': policy_area.name,
            'selectedOption': majority_option
        }, room=session_id)
        
        # Move to next policy
        socketio.sleep(2)
        discuss_policy_area(session_id, policy_index + 1)

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Clean up deliberation session on disconnect"""
        session_id = request.sid
        if session_id in deliberation_sessions:
            del deliberation_sessions[session_id]
            logging.info(f"Cleaned up deliberation session: {session_id}")