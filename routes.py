from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from game_data import POLICIES, validate_package, MAX_BUDGET
from ai_agents import generate_agents, agent_justify

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Route for the home page"""
    return render_template('index.html')

@main.route('/game')
def game():
    """Route for the game page"""
    return render_template('game.html')

@main.route('/phase1', methods=['GET', 'POST'])
def phase1():
    """
    Policy selection phase where user selects policy options within a budget
    """
    if request.method == 'POST':
        # Extract the selected policy options from the form
        selections = {}
        for policy in POLICIES:
            policy_name = policy['name']
            option_level = request.form.get(policy_name)
            if option_level:
                selections[policy_name] = int(option_level)
        
        # Validate the selections
        is_valid, total_cost, error_message = validate_package(selections)
        
        if is_valid:
            # Store the validated selections in the session
            session['player_package'] = selections
            session['package_cost'] = total_cost
            
            # Generate agents and store them in the session
            if 'agents' not in session:
                agents = generate_agents()
                session['agents'] = agents
                
            return redirect(url_for('main.phase2'))
        else:
            # Flash the error message
            flash(error_message, 'error')
    
    # Render the phase1 template with policy data
    return render_template('phase1.html', policies=POLICIES, max_budget=MAX_BUDGET)

@main.route('/phase2')
def phase2():
    """
    Next phase after policy selections
    """
    # Check if user has completed phase1
    if 'player_package' not in session:
        flash('Please complete the policy selections first', 'error')
        return redirect(url_for('main.phase1'))
    
    # Generate justifications for each agent and policy
    selections = session['player_package']
    agents = session.get('agents', [])
    
    # Create a dictionary to store justifications for each agent
    justifications = {}
    
    # Find the policy objects from their names
    policy_objects = {}
    for policy in POLICIES:
        policy_objects[policy['name']] = policy
    
    # Generate justifications for each agent
    for agent in agents:
        agent_id = agent['name']
        justifications[agent_id] = {}
        
        for policy_name, option_level in selections.items():
            # Get the full policy object
            policy = policy_objects.get(policy_name, {})
            
            # Generate a justification for this policy choice
            justification = agent_justify(policy_name, option_level, agent)
            justifications[agent_id][policy_name] = justification
    
    return render_template('phase2.html', 
                         selections=session['player_package'], 
                         cost=session['package_cost'],
                         max_budget=MAX_BUDGET,
                         justifications=justifications)