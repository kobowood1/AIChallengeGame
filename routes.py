from flask import Blueprint, render_template, request, session, redirect, url_for, flash, Response
from game_data import POLICIES, validate_package, MAX_BUDGET
from ai_agents import generate_agents, agent_justify
import markdown
import json
from datetime import datetime

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
    Policy discussion and voting phase
    """
    # Check if user has completed phase1
    if 'player_package' not in session:
        flash('Please complete the policy selections first', 'error')
        return redirect(url_for('main.phase1'))
    
    # Clear any existing agent votes (in case of returning to this page)
    if 'agent_votes' in session:
        session.pop('agent_votes')
    
    # Clear any existing final package (in case of returning to this page)
    if 'final_package' in session:
        session.pop('final_package')
    
    return render_template('phase2.html',
                         selections=session['player_package'], 
                         cost=session['package_cost'],
                         max_budget=MAX_BUDGET)

@main.route('/phase3')
def phase3():
    """
    Final implementation phase after voting
    """
    # Check if user has completed phase2
    if 'final_package' not in session:
        flash('Please complete the voting phase first', 'error')
        return redirect(url_for('main.phase2'))
    
    return render_template('phase3.html',
                         final_package=session['final_package'],
                         final_cost=session['final_cost'],
                         player_package=session['player_package'],
                         max_budget=MAX_BUDGET)

@main.route('/submit-reflection', methods=['POST'])
def submit_reflection():
    """
    Process the reflection form submission and generate a markdown report
    """
    # Check if user has completed the necessary phases
    if 'final_package' not in session or 'player_package' not in session:
        flash('Please complete the policy process first', 'error')
        return redirect(url_for('main.phase1'))
    
    # Extract form data
    form_data = request.form
    
    # Build the markdown report
    report = generate_markdown_report(form_data)
    
    # Create downloadable response
    response = Response(
        report,
        mimetype='text/markdown',
        headers={'Content-Disposition': 'attachment;filename=policy_reflection_report.md'}
    )
    
    return response

@main.route('/thank-you')
def thank_you():
    """
    Thank you page after submission
    """
    return render_template('thank_you.html')

def generate_markdown_report(form_data):
    """
    Generate a Markdown report containing participant data and reflections
    
    Args:
        form_data: Form data from the reflection submission
        
    Returns:
        str: Markdown formatted report
    """
    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the participant information
    participant_info = f"""# Policy Simulation Reflection Report

## Generated on: {current_time}

## Participant Information
- **Age:** {form_data.get('age', 'Not provided')}
- **Gender:** {form_data.get('gender', 'Not provided')}
- **Nationality:** {form_data.get('nationality', 'Not provided')}
- **Education Level:** {form_data.get('education', 'Not provided')}

"""
    
    # Format the policy packages
    player_package = session.get('player_package', {})
    final_package = session.get('final_package', {})
    player_cost = session.get('package_cost', 0)
    final_cost = session.get('final_cost', 0)
    
    policy_section = f"""## Policy Packages

### Original Proposal (Budget: {player_cost}/{MAX_BUDGET})
"""
    
    for policy_name, option_level in player_package.items():
        policy_section += f"- **{policy_name}:** Option {option_level}\n"
    
    policy_section += f"""
### Final Approved Package (Budget: {final_cost}/{MAX_BUDGET})
"""
    
    for policy_name, option_level in final_package.items():
        original_level = player_package.get(policy_name, 'N/A')
        if original_level != option_level:
            policy_section += f"- **{policy_name}:** Option {option_level} (Changed from {original_level})\n"
        else:
            policy_section += f"- **{policy_name}:** Option {option_level}\n"
    
    # Format the reflection responses
    reflection_section = """
## Reflection Responses

"""
    
    # Add each reflection question and answer
    questions = [
        "What factors influenced your initial policy selections?",
        "How did you feel about the voting process and the final policy package?",
        "What strategies did you use to persuade the AI agents during discussion?",
        "How did different ideological perspectives influence the policy decisions?",
        "What were the most challenging aspects of the policy-making process?",
        "How did budget constraints shape your decision-making?",
        "What did you learn about compromise and consensus-building?",
        "How did your perspective on policy-making change throughout this exercise?",
        "What aspects of real-world policy-making were simulated effectively, and what was missing?",
        "How might you apply insights from this simulation to real-world civic engagement?"
    ]
    
    for i, question in enumerate(questions):
        question_num = i + 1
        answer = form_data.get(f'q{question_num}', 'No response')
        reflection_section += f"### Q{question_num}: {question}\n\n{answer}\n\n"
    
    # Combine all sections
    full_report = participant_info + policy_section + reflection_section
    
    return full_report