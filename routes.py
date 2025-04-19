from flask import Blueprint, render_template, request, session, redirect, url_for, flash, Response
from game_data import POLICIES, validate_package, MAX_BUDGET
from ai_agents import generate_agents, agent_justify
import markdown
import json
import tempfile
from datetime import datetime
from weasyprint import HTML, CSS

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Route for the home page"""
    return render_template('index.html')

@main.route('/scenario')
def scenario():
    """Route for the Republic of Bean scenario context"""
    return render_template('scenario.html')

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
                         max_budget=MAX_BUDGET,
                         policies=POLICIES)

@main.route('/phase3')
def phase3():
    """
    Final implementation phase after voting
    """
    # Check if user has player_package (meaning they at least did phase 1)
    if 'player_package' not in session:
        flash('Please complete the policy selections first', 'error')
        return redirect(url_for('main.phase1'))
    
    # If final_package is not in session, use the player's package as a fallback
    # This can happen if Socket.IO events didn't properly update the session
    if 'final_package' not in session:
        session['final_package'] = session['player_package'].copy()
        # Calculate the cost of the player's package
        total_cost = 0
        for policy_name, option_level in session['player_package'].items():
            for policy in POLICIES:
                if policy['name'] == policy_name:
                    total_cost += policy['options'][option_level - 1]['cost']
                    break
        session['final_cost'] = total_cost
    
    return render_template('phase3.html',
                         final_package=session['final_package'],
                         final_cost=session['final_cost'],
                         player_package=session['player_package'],
                         max_budget=MAX_BUDGET,
                         policies=POLICIES)

@main.route('/submit-reflection', methods=['POST'])
def submit_reflection():
    """
    Process the reflection form submission and generate a report
    """
    # Check if user has completed the necessary phases
    if 'final_package' not in session or 'player_package' not in session:
        flash('Please complete the policy process first', 'error')
        return redirect(url_for('main.phase1'))
    
    # Extract form data
    form_data = request.form
    
    # Build the markdown report
    md_report = generate_markdown_report(form_data)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_report, extensions=['tables', 'fenced_code', 'nl2br'])
    
    # Style the HTML for better readability
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Policy Reflection Report</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6;
                margin: 2cm;
                color: #333;
                background-color: #fff;
            }}
            h1 {{ color: #2c3e50; font-size: 24px; margin-bottom: 20px; }}
            h2 {{ color: #3498db; font-size: 20px; margin-top: 30px; margin-bottom: 15px; }}
            h3 {{ color: #2980b9; font-size: 16px; margin-top: 25px; }}
            p {{ margin-bottom: 15px; }}
            ul {{ margin-bottom: 15px; }}
            li {{ margin-bottom: 5px; }}
            .policy-option {{ 
                padding: 5px 10px;
                background-color: #f8f9fa;
                border-left: 3px solid #3498db;
                margin-bottom: 5px;
            }}
            .changed {{
                border-left: 3px solid #e74c3c;
            }}
            .budget-info {{
                padding: 8px;
                background-color: #eef2f7;
                border-radius: 5px;
                display: inline-block;
                margin-bottom: 15px;
            }}
            @media print {{
                body {{
                    margin: 1cm;
                }}
                h1, h2, h3 {{
                    page-break-after: avoid;
                }}
                p, li {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Return as HTML with print-friendly styling
    response = Response(
        styled_html,
        mimetype='text/html',
        headers={'Content-Disposition': 'attachment;filename=policy_reflection_report.html'}
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
        "What emotions came up for you during the decision-making process—discomfort, frustration, detachment, guilt? What do those feelings reveal about your position in relation to refugee education?",
        "Did anything about your role in the game feel familiar—either from your personal or professional life? If so, how?",
        "What assumptions about refugees, policy, or education were challenged or reinforced during the game?",
        "How did the group dynamics impact your ability to advocate for certain policies? Were there moments when you chose silence or compromise? Why?",
        "Has your understanding of refugee education shifted from seeing it as a service 'for them' to a system embedded in broader struggles over power, identity, and justice? If so, how?",
        "Whose interests did your decisions ultimately serve—refugees, citizens, or the state? Why?",
        "What power did you assume you had as a policymaker—and who did you imagine was absent or voiceless in that process?",
        "What compromises did you make for the sake of consensus, and who or what got erased in the process?",
        "How did the structure of the game (budget, options, scenario) shape or limit your imagination of justice?",
        "If refugee education wasn't about inclusion into existing systems—but about transforming those systems—what would that look like, and did your decisions move toward or away from that?"
    ]
    
    for i, question in enumerate(questions):
        question_num = i + 1
        answer = form_data.get(f'q{question_num}', 'No response')
        reflection_section += f"### Q{question_num}: {question}\n\n{answer}\n\n"
    
    # Combine all sections
    full_report = participant_info + policy_section + reflection_section
    
    return full_report