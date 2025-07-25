from flask import Blueprint, render_template, request, session, redirect, url_for, flash, Response, get_flashed_messages
from flask_login import login_user, logout_user, login_required, current_user
from game_data import POLICIES, validate_package, MAX_BUDGET
from ai_agents import generate_agents, agent_justify
import markdown
import json
import tempfile
import uuid
import logging
from datetime import datetime
from weasyprint import HTML, CSS
from models import db, Participant, User, GameSession
from forms import LoginForm, RegistrationForm, ParticipantForm
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from email_utils import send_reflection_report
from openai_utils import generate_policy_profile

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Route for the home page - redirects to sign in"""
    if current_user.is_authenticated:
        # Check if user has an active game session
        active_session = GameSession.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        if active_session:
            # Redirect to appropriate phase based on progress
            if active_session.current_phase == 'registration':
                return redirect(url_for('main.register'))
            elif active_session.current_phase == 'scenario':
                return redirect(url_for('main.scenario'))
            elif active_session.current_phase == 'phase1':
                return redirect(url_for('main.card_selection'))
            elif active_session.current_phase == 'phase2':
                return redirect(url_for('main.phase2'))
            elif active_session.current_phase == 'phase3':
                return redirect(url_for('main.phase3'))
            elif active_session.current_phase == 'completed':
                return redirect(url_for('main.thank_you'))
        
        # No active session, redirect to dashboard
        return redirect(url_for('main.dashboard'))
    
    # Not authenticated, redirect to sign in page
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard for authenticated users"""
    # Check for any active game sessions
    active_session = GameSession.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).first()
    
    # Get completed sessions count
    completed_sessions = GameSession.query.filter_by(
        user_id=current_user.id, 
        is_active=False
    ).count()
    
    return render_template('dashboard.html', 
                         active_session=active_session,
                         completed_sessions=completed_sessions)

@main.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form)


@main.route('/register_user', methods=['GET', 'POST'])
def register_user():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('auth/register.html', form=form)


@main.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main.route('/start')
@login_required
def start():
    """Route to start a new game session"""
    # Create a new game session for the user
    new_session = GameSession(user_id=current_user.id)
    db.session.add(new_session)
    db.session.commit()
    
    # Store session info for game mechanics
    session['game_session_id'] = new_session.id
    session['session_token'] = new_session.session_token
    
    # Check if user has participant info from previous sessions
    existing_participant = Participant.query.filter_by(user_id=current_user.id).first()
    if existing_participant:
        # Copy participant info to session for game use
        session['participant_registered'] = True
        session['participant_info'] = {
            'age': existing_participant.age,
            'nationality': existing_participant.nationality,
            'occupation': existing_participant.occupation,
            'education_level': existing_participant.education_level,
            'displacement_experience': existing_participant.displacement_experience,
            'current_location_city': existing_participant.current_location_city,
            'current_location_country': existing_participant.current_location_country
        }
        return redirect(url_for('main.scenario'))
    else:
        # Need to collect participant info
        return redirect(url_for('main.register'))

@main.route('/reset')
@login_required
def reset():
    """Reset the current game session and start over"""
    # Mark current session as inactive
    if 'game_session_id' in session:
        game_session = GameSession.query.get(session['game_session_id'])
        if game_session:
            game_session.is_active = False
            db.session.commit()
    
    # Clear participant data from database
    existing_participant = Participant.query.filter_by(user_id=current_user.id).first()
    if existing_participant:
        db.session.delete(existing_participant)
        db.session.commit()
    
    # Clear the session
    session.clear()
    flash('Your game session has been reset. You can start fresh.', 'info')
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Route for participant demographic registration"""
    form = ParticipantForm()
    
    # Pre-populate form with existing participant data if available
    existing_participant = Participant.query.filter_by(user_id=current_user.id).first()
    if existing_participant and not form.is_submitted():
        form.age.data = existing_participant.age
        form.nationality.data = existing_participant.nationality
        form.occupation.data = existing_participant.occupation
        form.education_level.data = existing_participant.education_level
        form.displacement_experience.data = existing_participant.displacement_experience
        form.current_location_city.data = existing_participant.current_location_city
        form.current_location_country.data = existing_participant.current_location_country
    
    if form.validate_on_submit():
        try:
            # Generate a unique session ID if not already present
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            
            # Check if participant for this user already exists
            existing_participant = Participant.query.filter_by(user_id=current_user.id).first()
            if existing_participant:
                # Update existing participant
                participant = existing_participant
                participant.age = form.age.data
                participant.nationality = form.nationality.data
                participant.occupation = form.occupation.data
                participant.education_level = form.education_level.data
                participant.displacement_experience = form.displacement_experience.data
                participant.current_location_city = form.current_location_city.data
                participant.current_location_country = form.current_location_country.data
                participant.session_id = session['session_id']
            else:
                # Create new participant
                participant = Participant()
                participant.user_id = current_user.id
                participant.age = form.age.data
                participant.nationality = form.nationality.data
                participant.occupation = form.occupation.data
                participant.education_level = form.education_level.data
                participant.displacement_experience = form.displacement_experience.data
                participant.current_location_city = form.current_location_city.data
                participant.current_location_country = form.current_location_country.data
                participant.session_id = session['session_id']
                db.session.add(participant)
            
            # Add to database
            db.session.add(participant)
            db.session.commit()
            
            # Mark as registered in session
            session['participant_registered'] = True
            
            # Redirect to scenario page
            flash('Registration successful! Welcome to the Republic of Bean policy simulation.', 'success')
            return redirect(url_for('main.scenario'))
            
        except Exception as e:
            import logging
            logging.error(f"Registration error: {str(e)}", exc_info=True)
            flash(f'Registration error: {str(e)}', 'error')
            return render_template('register.html', form=form)
    
    # GET request - show registration form
    return render_template('register.html', form=form)

@main.route('/scenario')
def scenario():
    """Route for the Republic of Bean scenario context"""
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
        
    return render_template('scenario.html')

@main.route('/game')
def game():
    """Route for the game page"""
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
        
    return render_template('game.html')

@main.route('/card-selection', methods=['GET', 'POST'])
@main.route('/cards', methods=['GET', 'POST'])
def card_selection():
    """
    Card-based policy selection phase where user selects policy options within a budget
    """
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
    
    if request.method == 'POST':
        # Handle card selection submission
        card_data = request.get_json()
        
        # Extract the selected policy options from the card data
        selections = {}
        for policy_area, selection in card_data.get('selections', {}).items():
            selections[policy_area] = selection['option']
        
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
            
            # Update game session phase
            game_session = GameSession.query.filter_by(
                user_id=current_user.id, 
                is_active=True
            ).first()
            if game_session:
                game_session.current_phase = 'phase2'
                game_session.policy_selections = json.dumps(selections)
                db.session.commit()
            
            return {'success': True, 'redirect': url_for('main.phase2')}
        else:
            return {'success': False, 'error': error_message}, 400
    
    # GET request - show card selection interface
    return render_template('card_selection.html', policies=POLICIES, max_budget=MAX_BUDGET)

@main.route('/phase1', methods=['GET', 'POST'])
def phase1():
    """
    Legacy policy selection phase - redirects to card selection
    """
    return redirect(url_for('main.card_selection'))

@main.route('/phase2')
def phase2():
    """
    Policy discussion and voting phase - now using multi-agent system
    """
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
        
    # Check if user has completed phase1
    if 'player_package' not in session:
        flash('Please complete the policy selections first', 'error')
        return redirect(url_for('main.card_selection'))
    
    # Redirect to multi-agent discussion (this replaces the old Phase 2)
    return redirect(url_for('multi_agent.phase2_multi_agent'))

@main.route('/phase3')
def phase3():
    """
    Final implementation phase after voting
    """
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
        
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
    
    # Get participant information from the database for the OpenAI profile
    participant_info = None
    if 'session_id' in session:
        participant = Participant.query.filter_by(session_id=session['session_id']).first()
        if participant:
            participant_info = {
                'age': participant.age,
                'nationality': participant.nationality,
                'occupation': participant.occupation,
                'education_level': participant.education_level
            }
    
    # Generate a policy profile using OpenAI
    policy_profile = generate_policy_profile(
        session['player_package'], 
        session['final_package'],
        participant_info
    )
    
    return render_template('phase3.html',
                         final_package=session['final_package'],
                         final_cost=session['final_cost'],
                         player_package=session['player_package'],
                         max_budget=MAX_BUDGET,
                         policies=POLICIES,
                         policy_profile=policy_profile)

@main.route('/submit-reflection', methods=['GET', 'POST'])
def submit_reflection():
    """
    Process the reflection form submission and generate a report
    """
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
        
    # Check if user has completed the necessary phases
    if 'final_package' not in session or 'player_package' not in session:
        flash('Please complete the policy process first', 'error')
        return redirect(url_for('main.phase1'))
    
    # Handle GET request from thank-you page for downloading report again
    if request.method == 'GET' and request.args.get('download') == 'true':
        # Build the markdown report using the stored session data
        # This works if the user navigates back to thank-you page and downloads again
        form_data = {}
        md_report = generate_markdown_report(form_data)
        html_content = markdown.markdown(md_report, extensions=['tables', 'fenced_code', 'nl2br'])
        
        # Return the styled HTML as a download
        styled_html = create_styled_html(html_content)
        response = Response(
            styled_html,
            mimetype='text/html',
            headers={'Content-Disposition': 'attachment;filename=policy_reflection_report.html'}
        )
        return response
    
    # Extract form data for POST requests
    form_data = request.form
    
    # Build the markdown report
    md_report = generate_markdown_report(form_data)
    
    # Get participant information from the database
    participant_info = None
    participant_id = session.get('session_id', str(uuid.uuid4()))
    if 'session_id' in session:
        participant = Participant.query.filter_by(session_id=session['session_id']).first()
        if participant:
            participant_info = {
                'age': participant.age,
                'nationality': participant.nationality,
                'occupation': participant.occupation,
                'education_level': participant.education_level,
                'current_location_city': participant.current_location_city,
                'current_location_country': participant.current_location_country
            }
    
    # Send the reflection report via email
    try:
        email_sent = send_reflection_report(participant_info, md_report, participant_id)
        if email_sent:
            # Message for successful email delivery
            flash('Your report has been successfully generated and sent to the research team via email. ' +
                  'A copy has also been saved to the database for research purposes. ' +
                  'You can download your personal copy using the button below.', 'success')
        else:
            # Error message that explains emails may have failed but data is still saved
            flash('There was an issue sending the report via email, but your report has been generated and saved. ' +
                  'The research team will still receive your submissions through the database.', 'warning')
            logging.warning("Email couldn't be sent, but report was generated and stored in database")
    except Exception as e:
        # General error message
        flash('Your report has been successfully generated and saved in our system. ' +
              'There was an unexpected issue with email delivery, but your data is securely stored.', 'info')
        logging.error(f"Email error: {str(e)}", exc_info=True)
    
    # Store the report in the session so we can access it later
    session['reflection_report'] = md_report
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_report, extensions=['tables', 'fenced_code', 'nl2br'])
    
    # Style the HTML for better readability using the helper function
    styled_html = create_styled_html(html_content)
    
    # Check if we should download immediately or redirect to thank you page
    if request.form.get('action') == 'download':
        # Return as HTML with print-friendly styling for immediate download
        response = Response(
            styled_html,
            mimetype='text/html',
            headers={'Content-Disposition': 'attachment;filename=policy_reflection_report.html'}
        )
        return response
    else:
        # Redirect to thank you page
        return redirect(url_for('main.thank_you'))

@main.route('/thank-you')
def thank_you():
    """
    Thank you page after submission
    """
    # Check if user is registered
    if 'participant_registered' not in session or not session['participant_registered']:
        flash('Please register before accessing the simulation.', 'warning')
        return redirect(url_for('main.register'))
    
    # If there are no flash messages already, provide a default success message
    if not get_flashed_messages():
        flash('Your report has been successfully generated and recorded in our system. Thank you for your participation!', 'success')
        
    return render_template('thank_you.html')

def create_styled_html(html_content):
    """
    Create a styled HTML document from HTML content
    
    Args:
        html_content: HTML content to style
        
    Returns:
        str: Styled HTML document
    """
    return f"""
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
    
    # Get participant information from the database
    participant = None
    if 'session_id' in session:
        participant = Participant.query.filter_by(session_id=session['session_id']).first()
    
    # Format the participant information
    participant_section = f"""# Policy Simulation Reflection Report

## Generated on: {current_time}

## Participant Information
"""
    
    if participant:
        participant_section += f"""- **Age:** {participant.age}
- **Nationality:** {participant.nationality}
- **Occupation:** {participant.occupation}
- **Education Level:** {participant.education_level}
- **Current Location:** {participant.current_location_city}, {participant.current_location_country}
"""
        if participant.displacement_experience:
            participant_section += f"- **Displacement Experience:** {participant.displacement_experience}\n"
    else:
        participant_section += "- Participant information not available\n"
    
    participant_section += "\n"
    
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
    
    # Generate policy profile if not already in session
    if 'policy_profile' not in session:
        # Get participant information from the database for the OpenAI profile
        participant_info = None
        if participant:
            participant_info = {
                'age': participant.age,
                'nationality': participant.nationality,
                'occupation': participant.occupation,
                'education_level': participant.education_level
            }
        
        # Generate a policy profile using OpenAI
        from openai_utils import generate_policy_profile
        profile = generate_policy_profile(
            player_package, 
            final_package,
            participant_info
        )
        session['policy_profile'] = profile
    
    # Add the policy profile section
    policy_profile = session.get('policy_profile', 'Policy profile could not be generated.')
    policy_section += f"""
### Policy Profile Analysis
{policy_profile}
"""
    
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
    full_report = participant_section + policy_section + reflection_section
    
    return full_report