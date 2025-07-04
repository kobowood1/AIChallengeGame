"""
Routes for the multi-agent policy simulation integration
"""
import time
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from multi_agent_system import MultiAgentSimulation, create_policy_simulation_data
import json

multi_agent_bp = Blueprint('multi_agent', __name__)

@multi_agent_bp.route('/phase2_multi_agent')
@login_required
def phase2_multi_agent():
    """Enhanced Phase 2 with multi-agent simulation"""
    
    # Get user's policy selections from session (try multiple possible keys)
    selections = session.get('policy_selections', {})
    if not selections:
        selections = session.get('selections', {})
    if not selections:
        selections = session.get('player_package', {})
    if not selections:
        # Create demo selections for testing if no real selections exist
        selections = {
            'Access to Education': 2,
            'Language Instruction': 1, 
            'Teacher Training': 3,
            'Curriculum Adaptation': 2,
            'Psychosocial Support': 1,
            'Financial Support': 2,
            'Certification & Accreditation': 1
        }
        print("No user selections found, using demo data for multi-agent discussion")
    
    # Store selections in consistent format for multi-agent system
    session['policy_selections'] = selections
    
    # Initialize multi-agent simulation
    if 'multi_agent_sim' not in session:
        session['multi_agent_sim'] = {
            'initialized': True,
            'current_agent_index': 0,
            'agents_order': ['Amir', 'Salma', 'Lila', 'Leila'],
            'user_responses': [],
            'conversation_history': [],
            'waiting_for_user': False,
            'phase_complete': False
        }
    
    # Create simulation instance
    simulation = MultiAgentSimulation()
    
    # Set up policy context (focusing on Access to Education for demo)
    policy_data = create_policy_simulation_data()
    user_vote = session.get('user_policy_reasoning', {}).get('Access to Education', 
                           'Integration with Quotas because it balances resource costs and inclusivity')
    
    simulation.set_policy_context(
        policy_data["policy_area"],
        policy_data["options"],
        user_vote
    )
    
    # Get current simulation state
    sim_state = session['multi_agent_sim']
    
    # Generate initial moderator message if starting
    if not sim_state.get('moderator_intro_sent'):
        intro = simulation.generate_moderator_intro()
        sim_state['moderator_intro'] = intro
        sim_state['moderator_intro_sent'] = True
        session['multi_agent_sim'] = sim_state
    
    # Get policy data for template rendering
    from game_data import POLICIES
    
    return render_template('phase2_multi_agent.html',
                         user_selections=selections,
                         policy_data=POLICIES,
                         selections=selections,
                         policy_options=policy_data["options"],
                         user_vote=user_vote,
                         sim_state=sim_state,
                         moderator_intro=sim_state.get('moderator_intro', ''))

@multi_agent_bp.route('/api/multi_agent/next_turn', methods=['POST'])
@login_required 
def next_agent_turn():
    """Trigger the next agent to speak"""
    
    data = request.get_json()
    user_response = data.get('user_response', '')
    
    sim_state = session.get('multi_agent_sim', {})
    if not sim_state.get('initialized'):
        return jsonify({'error': 'Simulation not initialized'}), 400
    
    # Create simulation instance
    simulation = MultiAgentSimulation()
    
    # Set up context
    policy_data = create_policy_simulation_data()
    user_vote = session.get('user_policy_reasoning', {}).get('Access to Education',
                           'Integration with Quotas because it balances resource costs and inclusivity')
    
    simulation.set_policy_context(
        policy_data["policy_area"],
        policy_data["options"], 
        user_vote
    )
    
    # Restore conversation history
    simulation.conversation_history = sim_state.get('conversation_history', [])
    
    current_index = sim_state.get('current_agent_index', 0)
    agents_order = sim_state.get('agents_order', ['Amir', 'Salma', 'Lila', 'Leila'])
    
    # Store user response if provided
    if user_response.strip():
        sim_state['user_responses'].append(user_response)
        simulation.conversation_history.append(f"User: {user_response}")
    
    # Check if all agents have spoken
    if current_index >= len(agents_order):
        # Generate final moderator summary
        summary = simulation.generate_moderator_summary(sim_state['user_responses'])
        sim_state['final_summary'] = summary
        sim_state['phase_complete'] = True
        session['multi_agent_sim'] = sim_state
        
        return jsonify({
            'type': 'moderator_summary',
            'message': summary,
            'phase_complete': True
        })
    
    # Get next agent response
    agent_name = agents_order[current_index]
    context = f"The user voted for {user_vote}. Previous user response: {user_response}"
    
    try:
        agent_response = simulation.generate_agent_response(agent_name, context)
        
        # Update simulation state
        sim_state['current_agent_index'] = current_index + 1
        sim_state['conversation_history'] = simulation.conversation_history
        sim_state['waiting_for_user'] = True
        session['multi_agent_sim'] = sim_state
        
        return jsonify({
            'type': 'agent_response',
            'agent_name': agent_name,
            'message': agent_response,
            'waiting_for_user': True,
            'progress': f"{current_index + 1}/{len(agents_order)}",
            'debug': f"Agent {agent_name} responded successfully"
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate agent response: {str(e)}'}), 500

@multi_agent_bp.route('/api/multi_agent/accept_recommendation', methods=['POST'])
@login_required
def accept_recommendation():
    """Handle user accepting the group recommendation"""
    try:
        # Get the final policy package from the multi-agent simulation
        sim_state = session.get('multi_agent_sim', {})
        selections = session.get('policy_selections', {})
        
        # Store final package in session for Phase 3
        session['final_package'] = selections.copy()
        session['agent_votes'] = selections.copy()  # For compatibility with existing Phase 3
        
        # Calculate total cost for display
        from game_data import POLICIES
        total_cost = 0
        for policy_name, option_level in selections.items():
            for policy in POLICIES:
                if policy['name'] == policy_name:
                    total_cost += policy['options'][option_level - 1]['cost']
                    break
        session['final_cost'] = total_cost
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('main.phase3')
        })
        
    except Exception as e:
        print(f"Error accepting recommendation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@multi_agent_bp.route('/api/multi_agent/final_decision', methods=['POST'])
@login_required
def submit_final_decision():
    """Submit the final group decision"""
    
    data = request.get_json()
    final_choice = data.get('final_choice', '')
    reasoning = data.get('reasoning', '')
    
    # Store the final decision
    import time
    session['final_group_decision'] = {
        'choice': final_choice,
        'reasoning': reasoning,
        'timestamp': time.time()
    }
    
    # Mark simulation as complete
    sim_state = session.get('multi_agent_sim', {})
    sim_state['decision_submitted'] = True
    session['multi_agent_sim'] = sim_state
    
    return jsonify({
        'success': True,
        'message': 'Final decision recorded successfully',
        'redirect_url': url_for('main.phase3')
    })

@multi_agent_bp.route('/api/multi_agent/reset')
@login_required
def reset_simulation():
    """Reset the multi-agent simulation"""
    
    if 'multi_agent_sim' in session:
        del session['multi_agent_sim']
    
    return jsonify({'success': True, 'message': 'Simulation reset'})