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
    """Structured Phase 2 with stepwise moderated multi-agent deliberation"""
    
    # Get user's policy selections from session
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
            'Certification / Accreditation of Previous Education': 1
        }
        print("No user selections found, using demo data for multi-agent discussion")
    
    # Store selections in consistent format for multi-agent system
    session['policy_selections'] = selections
    
    # Get user name for personalization - use first name if available, otherwise username
    if current_user.is_authenticated:
        user_name = current_user.first_name if current_user.first_name else current_user.username
    else:
        user_name = 'Participant'
    session['user_name'] = user_name
    
    # Initialize agent names and policies for structured deliberation
    import random
    
    # Always regenerate agent names for diversity (remove persistent session storage)
    if True:  # Force regeneration each time
        # Pool of available agent names
        available_names = [
            'Alex', 'Maya', 'Jordan', 'Sam', 'Casey', 'Taylor', 'Morgan', 'Riley',
            'Priya', 'Chen', 'Fatima', 'Kofi', 'Elena', 'Hiroshi', 'Amara', 'Luca',
            'Zara', 'Kai', 'Noor', 'Diego', 'Anya', 'Tomas', 'Leila', 'Jin',
            'Sofia', 'Arjun', 'Mia', 'Omar', 'Chloe', 'Ravi', 'Zoe', 'Malik',
            'Luna', 'Hassan', 'Isla', 'Yuki', 'Emilia', 'Kwame', 'Sienna', 'Liam'
        ]
        
        # Randomly select 4 names for this session
        agent_names = random.sample(available_names, 4)
        session['agent_names'] = agent_names
        
        # Generate strategic agent policy choices with guaranteed diversity
        policy_areas = [
            'Access to Education',
            'Language Instruction', 
            'Teacher Training',
            'Curriculum Adaptation',
            'Psychosocial Support',
            'Financial Support',
            'Certification & Accreditation'
        ]
        
        # Define distinct agent archetypes with strategic preferences
        agent_archetypes = [
            {
                'name': 'progressive',
                'description': 'Progressive - believes in comprehensive support and integration',
                'preferences': [3, 3, 2, 3, 3, 2, 2],  # High investment in most areas
                'variations': [-1, 0, 1]  # Allow some variation
            },
            {
                'name': 'pragmatic', 
                'description': 'Pragmatic - focuses on practical implementation and measurable outcomes',
                'preferences': [2, 2, 3, 2, 2, 1, 2],  # Balanced with emphasis on teacher training
                'variations': [-1, 0, 1]
            },
            {
                'name': 'collaborative',
                'description': 'Collaborative - emphasizes community engagement and shared responsibility', 
                'preferences': [2, 1, 2, 1, 3, 2, 3],  # Focus on support and recognition
                'variations': [0, 1]
            },
            {
                'name': 'humanitarian',
                'description': 'Humanitarian - prioritizes individual student needs and wellbeing',
                'preferences': [3, 2, 1, 2, 3, 3, 1],  # High on care, mixed on systems
                'variations': [-1, 0, 1]
            }
        ]
        
        agent_policies = {}
        for i, agent_name in enumerate(agent_names):
            archetype = agent_archetypes[i % len(agent_archetypes)]
            agent_policy = {}
            
            for j, policy_area in enumerate(policy_areas):
                base_choice = archetype['preferences'][j]
                # Add variation to prevent identical choices
                variation = random.choice(archetype['variations'])
                final_choice = max(1, min(3, base_choice + variation))
                agent_policy[policy_area] = final_choice
            
            agent_policies[agent_name] = agent_policy
        session['agent_policies'] = agent_policies
    
    # Return the new structured deliberation template
    return render_template('phase2_multi_agent_new.html',
                         user_selections=selections,
                         user_name=user_name,
                         agent_names=session.get('agent_names', []),
                         agent_policies=session.get('agent_policies', {}))

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