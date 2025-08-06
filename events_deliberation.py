"""
Socket.IO event handlers for structured multi-agent policy deliberation
"""
import time
import logging
from flask import session, request
from flask_socketio import emit, join_room, leave_room
from multi_agent_system import MultiAgentSimulation
from challenge_content import POLICY_AREAS
from content_moderation import content_moderator
from openai import OpenAI
import os

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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

def generate_moderator_followup(policy_area_name, user_choice, user_reasoning, user_name):
    """Generate an engaging moderator follow-up that questions the user's reasoning"""
    try:
        system_prompt = f"""You are the Moderator of a refugee education policy simulation for the Republic of Bean. 
        
        A participant just explained why they chose a particular policy option. Your role is to:
        1. Acknowledge their reasoning respectfully
        2. Ask 1-2 thoughtful, challenging questions that make them think deeper
        3. Encourage them to consider alternative perspectives or potential challenges
        4. Keep it engaging and Socratic, not confrontational
        
        You should sound like an experienced policy facilitator who wants to deepen the discussion.
        Keep your response to 2-3 sentences maximum."""

        context_prompt = f"""Policy Area: {policy_area_name}
        User's Choice: Option {user_choice}
        User's Reasoning: "{user_reasoning}"
        
        Generate a moderator response that acknowledges {user_name}'s reasoning and asks probing questions to deepen their thinking about this policy choice. Make it conversational and engaging."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_prompt}
            ],
            max_tokens=150,
            temperature=0.7,
            timeout=10  # 10 second timeout to prevent socket issues
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logging.error(f"Error generating moderator followup: {e}")
        # Fallback to template-based responses
        fallback_responses = [
            f"Interesting perspective, {user_name}. What potential challenges might arise with that approach?",
            f"Thank you for that reasoning, {user_name}. How do you think other stakeholders might view this choice?",
            f"That's a thoughtful explanation, {user_name}. What evidence would you point to that supports this direction?",
            f"I appreciate your reasoning, {user_name}. How might this choice impact different groups within our community?"
        ]
        import random
        return random.choice(fallback_responses)

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
    
    @socketio_instance.on('user_message')
    def handle_user_message(data):
        """Handle user messages during deliberation with content moderation"""
        session_id = request.sid
        delib_session = deliberation_sessions.get(session_id)
        if not delib_session:
            return
        
        message = data.get('message', '')
        step = data.get('step', 0)
        policy_index = data.get('policyIndex', 0)
        
        # Content moderation check
        moderation_result = content_moderator.analyze_content(message)
        
        if moderation_result['is_harmful']:
            # Send moderator intervention
            moderator_response = moderation_result['response']
            logging.warning(f"Content moderation triggered for user {delib_session.user_name}: {moderation_result['category']} - {moderation_result['severity']}")
            
            emit('moderator_intervention', {
                'message': moderator_response,
                'type': 'content_guidance',
                'severity': moderation_result['severity']
            }, room=session_id)
            
            # Record the intervention in conversation history
            delib_session.conversation_history.append({
                'sender': 'Moderator',
                'message': f"[Moderation] {moderator_response}",
                'timestamp': time.time(),
                'type': 'moderation'
            })
            
            # Also record the user's flagged message for context
            delib_session.conversation_history.append({
                'sender': delib_session.user_name,
                'message': f"[Flagged] {message}",
                'timestamp': time.time(),
                'flagged': True
            })
            
            # Don't process the harmful message further, wait for user to respond appropriately
            return
        
        # Record message in conversation history (if not harmful)
        delib_session.conversation_history.append({
            'sender': delib_session.user_name,
            'message': message,
            'timestamp': time.time()
        })
        
        current_step = delib_session.get_current_step()
        
        if current_step == 'user_introduction':
            # User has introduced themselves, move to policy deliberation
            try:
                start_policy_deliberation(session_id)
            except Exception as e:
                logging.error(f"Error starting policy deliberation: {e}")
                # Continue anyway to prevent blocking
                emit('moderator_message', {
                    'message': "Let's begin our policy discussion.",
                    'step': 4,
                    'progress': 'Step 4: Policy Deliberation'
                }, room=session_id)
                emit('system_message', {
                    'message': f"Error starting policy deliberation: {str(e)}. Please refresh the page."
                }, room=session_id)
        elif current_step == 'policy_deliberation':
            # User explained their choice, moderator responds with follow-up questions
            policy_area = delib_session.get_policy_area(policy_index)
            if not policy_area:
                return
            
            # Generate moderator response to user's reasoning
            user_choice = delib_session.get_user_choice(policy_area.name)
            moderator_response = generate_moderator_followup(
                policy_area.name, 
                user_choice, 
                message, 
                delib_session.user_name
            )
            
            emit('moderator_message', {
                'message': moderator_response,
                'step': 4
            }, room=session_id)
            
            # After moderator questions, proceed to voting
            socketio.sleep(2)
            emit('moderator_message', {
                'message': f"Now let's proceed to the democratic vote on {policy_area.name}.",
                'step': 4
            }, room=session_id)
            
            # Start voting after brief delay
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
        
        logging.info(f"Vote completed for {policy_area.name}: Option {majority_option}")
        logging.info(f"Current final package: {delib_session.final_package}")
        
        emit('vote_result', {
            'message': f"Majority selected Option {majority_option}.",
            'policyArea': policy_area.name,
            'selectedOption': majority_option
        }, room=session_id)
        
        # Move to next policy with minimal delay
        socketio.sleep(1)
        discuss_policy_area(session_id, policy_index + 1)
    
    @socketio_instance.on('connect')
    def handle_connect():
        """Handle client connection with improved error handling"""
        session_id = request.sid
        logging.debug(f"Client connected: {session_id}")
        
        # Send connection confirmation
        emit('connection_status', {'status': 'connected'})
    
    @socketio_instance.on('ping')
    def handle_ping():
        """Handle ping to maintain connection"""
        emit('pong')
    
    @socketio_instance.on('reconnect_session')
    def handle_reconnect():
        """Handle session reconnection"""
        session_id = request.sid
        logging.info(f"Session reconnect attempt: {session_id}")
        
        # Check if deliberation session exists
        if session_id in deliberation_sessions:
            emit('session_restored', {'status': 'success'})
        else:
            emit('session_restored', {'status': 'new_session'})
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Clean up deliberation session on disconnect"""
        session_id = request.sid
        if session_id in deliberation_sessions:
            del deliberation_sessions[session_id]
            logging.info(f"Cleaned up deliberation session: {session_id}")

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
    
    # Generate agent introductions with minimal delays
    for i, agent_name in enumerate(delib_session.agent_names):
        # Show typing indicator before each introduction
        emit('agent_typing', {'agent': agent_name}, room=session_id)
        
        if i > 0:  # Small delay only between agents, not before first
            socketio.sleep(1)
        else:
            socketio.sleep(0.5)  # Initial delay to show typing
        
        # Generate agent profile intro
        agent_profile = delib_session.simulation.agents[agent_name]
        age = 35 + (i * 5)  # Simple age assignment
        
        # Get agent's policy summary
        policy_summary = generate_policy_summary(agent_name, delib_session.agent_policies.get(agent_name, {}))
        
        intro_text = (
            f"Hello! I'm {agent_name}, {age}, {agent_profile.background}. "
            f"My policy approach focuses on {policy_summary}."
        )
        
        # Hide typing and emit agent message
        emit('agent_stop_typing', {}, room=session_id)
        emit('agent_message', {
            'sender': agent_name,
            'message': intro_text,
            'agentType': agent_profile.model_type
        }, room=session_id)
    
    # Move to user introduction with minimal delay
    socketio.sleep(1)
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
    logging.info(f"Starting policy deliberation for session {session_id}")
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        logging.error(f"No deliberation session found for {session_id}")
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
    logging.info(f"Starting discussion of policy area 0 for session {session_id}")
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
    logging.info(f"Getting agent policy responses for session {session_id}, policy {policy_area.name}")
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        logging.error(f"No deliberation session found for {session_id}")
        return
    
    agent_choices = {}
    
    # Generate all agent responses more efficiently 
    for i, agent_name in enumerate(delib_session.agent_names):
        logging.info(f"Getting response from agent {agent_name}")
        
        # Show typing indicator before each agent responds
        emit('agent_typing', {'agent': agent_name}, room=session_id)
        
        # Small delay between agents for realism
        if i > 0:
            socketio.sleep(0.5)
        else:
            socketio.sleep(1)  # Longer delay before first agent to show typing
        
        agent_choice = delib_session.get_agent_choice(agent_name, policy_area.name)
        agent_choices[agent_name] = agent_choice
        
        # Generate rationale using AI with timeout protection
        agent_profile = delib_session.simulation.agents[agent_name]
        
        # Create agent dict for AI generation
        agent_dict = {
            'name': agent_name,
            'age': 35 + (delib_session.agent_names.index(agent_name) * 5),
            'occupation': agent_profile.background,
            'education_level': 'Bachelor\'s Degree',
            'socioeconomic_status': 'Middle Class',
            'ideology': agent_profile.ideology,
            'llm_model': agent_profile.model_type
        }
        
        # Define fallback responses upfront for faster access
        diverse_fallbacks = {
            1: {
                'conservative': f"I chose Option 1 because fiscal responsibility is key. We can't overspend on programs that might not deliver results.",
                'moderate': f"Option 1 makes sense - it's a pragmatic start that we can build upon once we see what works.",
                'liberal': f"While I'd prefer more support, Option 1 at least gets us moving in the right direction.",
                'humanitarian': f"Option 1 provides essential basics. Sometimes simple solutions work best for urgent needs."
            },
            2: {
                'conservative': f"Option 2 offers reasonable investment without excessive government expansion.",
                'moderate': f"I believe Option 2 strikes the right balance between helping students and managing costs.",
                'liberal': f"Option 2 provides meaningful support while staying politically feasible.",
                'humanitarian': f"Option 2 addresses core needs comprehensively - it's what these students deserve."
            },
            3: {
                'conservative': f"Though expensive, Option 3 could prevent larger social costs down the road.",
                'moderate': f"Option 3 represents a significant commitment, but some issues require bold action.",
                'liberal': f"Option 3 is essential - we cannot shortchange refugee students' futures.",
                'humanitarian': f"Option 3 is the only ethical choice. These students have already suffered enough."
            }
        }
        
        # Use AI with fallback on any issue to prevent blocking
        response_text = None
        try:
            from ai_agents import agent_justify
            
            response_text = agent_justify(
                policy_domain=policy_area.name,
                option_chosen=agent_choice,
                agent=agent_dict,
                user_message="",
                recent_messages=[],
                responding_to_agent=None
            )
            
        except Exception as e:
            logging.warning(f"AI generation failed for {agent_name}, using fallback: {e}")
            
            ideology_key = agent_profile.ideology.lower()
            if ideology_key not in diverse_fallbacks[agent_choice]:
                ideology_key = 'moderate'
            
            response_text = diverse_fallbacks[agent_choice][ideology_key]
        
        logging.info(f"Generated response for {agent_name}: {response_text[:50]}...")
        
        # Hide typing and emit agent message
        emit('agent_stop_typing', {}, room=session_id)
        emit('agent_message', {
            'sender': agent_name,
            'message': response_text,
            'agentType': agent_profile.model_type
        }, room=session_id)
    
    # Ask user for their choice with minimal delay
    socketio.sleep(1)
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
    
    # Always proceed to voting after user explains - this ensures democratic process
    # and meaningful deliberation on every policy area

def start_voting(session_id, policy_area):
    """Start voting process for a policy area with strategic agent voting"""
    delib_session = deliberation_sessions.get(session_id)
    if not delib_session:
        return
    
    emit('start_voting', {
        'message': f"Time to vote on {policy_area.name}. Each participant will cast their vote.",
        'policyArea': policy_area.name
    }, room=session_id)
    
    # Introduce strategic voting dynamics - agents might change their positions
    # based on discussion or compromise for the sake of group consensus
    import random
    
    for agent_name in delib_session.agent_names:
        original_choice = delib_session.get_agent_choice(agent_name, policy_area.name)
        
        # 30% chance an agent might shift their vote slightly for strategic reasons
        if random.random() < 0.3:
            # Agents might compromise toward more popular options or away from extreme positions
            user_choice = delib_session.get_user_choice(policy_area.name)
            other_agent_choices = [delib_session.get_agent_choice(other_name, policy_area.name) 
                                 for other_name in delib_session.agent_names if other_name != agent_name]
            
            # Calculate what seems to be the emerging consensus
            all_other_choices = [user_choice] + other_agent_choices
            if all_other_choices:
                avg_choice = sum(all_other_choices) / len(all_other_choices)
                
                # Agent might move slightly toward consensus (but not completely abandon their position)
                if abs(original_choice - avg_choice) > 1:
                    if original_choice < avg_choice:
                        final_vote = min(3, original_choice + 1)
                    else:
                        final_vote = max(1, original_choice - 1)
                else:
                    final_vote = original_choice
            else:
                final_vote = original_choice
        else:
            final_vote = original_choice
        
        delib_session.add_vote(agent_name, final_vote)
        
        # Occasionally announce vote changes for realism
        if final_vote != original_choice:
            emit('agent_message', {
                'sender': agent_name,
                'message': f"After hearing everyone's perspectives, I'm voting for Option {final_vote}.",
                'agentType': delib_session.simulation.agents[agent_name].model_type
            }, room=session_id)
            socketio.sleep(0.8)
    
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
    
    # Store final package in session with proper cost calculation
    session['final_package'] = delib_session.final_package.copy()
    
    # Calculate the cost of the final package using POLICY_AREAS
    total_cost = 0
    for policy_name, option_level in delib_session.final_package.items():
        for policy_area in POLICY_AREAS:
            if policy_area.name == policy_name:
                total_cost += policy_area.options[option_level - 1].cost
                break
    session['final_cost'] = total_cost
    
    # Also store as policy_selections for backup compatibility
    session['policy_selections'] = delib_session.final_package.copy()
    
    # Debug logging - detailed breakdown
    logging.info(f"=== FINAL PACKAGE STORAGE ===")
    logging.info(f"Session ID: {session_id}")
    logging.info(f"Delib session final_package: {delib_session.final_package}")
    logging.info(f"Stored in session['final_package']: {session['final_package']}")
    logging.info(f"Stored in session['policy_selections']: {session['policy_selections']}")
    logging.info(f"Player original package: {session.get('player_package', 'NOT SET')}")
    logging.info(f"Final cost calculated: {total_cost}")
    logging.info("=== END DEBUG ===")
    
    # Ensure session is committed
    session.modified = True