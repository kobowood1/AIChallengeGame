from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json
import io
import zipfile
from markupsafe import Markup

from models import db, Admin, User, GameSession, Participant
from forms import AdminLoginForm

# Create admin blueprint
admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in as an administrator to access this page.', 'error')
            return redirect(url_for('admin.admin_login'))
        if not isinstance(current_user, Admin):
            flash('Administrator access required.', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard with player statistics"""
    # Get overall statistics
    total_users = User.query.count()
    total_sessions = GameSession.query.count()
    completed_sessions = GameSession.query.filter_by(current_phase='completed').count()
    active_sessions = GameSession.query.filter_by(is_active=True).count()
    
    # Get recent activity
    recent_sessions = GameSession.query.order_by(desc(GameSession.last_activity)).limit(10).all()
    
    # Get completion rate by day (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    completion_data = db.session.query(
        func.date(GameSession.completed_at).label('date'),
        func.count(GameSession.id).label('count')
    ).filter(
        GameSession.completed_at >= thirty_days_ago,
        GameSession.current_phase == 'completed'
    ).group_by(func.date(GameSession.completed_at)).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_sessions=total_sessions,
                         completed_sessions=completed_sessions,
                         active_sessions=active_sessions,
                         recent_sessions=recent_sessions,
                         completion_data=completion_data)

@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route"""
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.admin_dashboard'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin_user = Admin.query.filter_by(username=form.username.data).first()
        if admin_user and admin_user.check_password(form.password.data):
            login_user(admin_user, remember=form.remember_me.data)
            admin_user.last_login = datetime.utcnow()
            # Mark this as an admin session
            session['user_type'] = 'admin'
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/admin'):
                next_page = url_for('admin.admin_dashboard')
            return redirect(next_page)
        else:
            flash('Invalid admin username or password', 'error')
    
    return render_template('admin/login.html', form=form)

@admin.route('/logout')
@admin_required
def admin_logout():
    """Admin logout route"""
    logout_user()
    # Clear the admin session marker
    session.pop('user_type', None)
    flash('You have been logged out from the admin panel.', 'info')
    return redirect(url_for('admin.admin_login'))

@admin.route('/players')
@admin_required
def player_list():
    """List all players with detailed information"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    # Base query with joins
    query = db.session.query(User).join(GameSession, User.id == GameSession.user_id, isouter=True)
    
    # Apply search filter
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    # Get paginated results
    users_query = query.distinct()
    total = users_query.count()
    users = users_query.offset((page - 1) * 20).limit(20).all()
    
    # Create pagination object manually
    class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page * per_page < total
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    users_pagination = SimplePagination(users, page, 20, total)
    
    # Get additional stats for each user
    user_stats = {}
    for user in users_pagination.items:
        sessions = GameSession.query.filter_by(user_id=user.id).all()
        completed_sessions = [s for s in sessions if s.current_phase == 'completed']
        user_stats[user.id] = {
            'total_sessions': len(sessions),
            'completed_sessions': len(completed_sessions),
            'last_activity': max([s.last_activity for s in sessions], default=None),
            'current_phase': sessions[-1].current_phase if sessions else None
        }
    
    return render_template('admin/player_list.html', 
                         users=users_pagination, 
                         user_stats=user_stats,
                         search=search)

@admin.route('/player/<int:user_id>')
@admin_required
def player_detail(user_id):
    """Detailed view of a specific player"""
    user = User.query.get_or_404(user_id)
    participant = Participant.query.filter_by(user_id=user_id).first()
    sessions = GameSession.query.filter_by(user_id=user_id).order_by(desc(GameSession.started_at)).all()
    
    # Parse JSON data for display
    session_data = []
    for session in sessions:
        data = {
            'session': session,
            'policy_selections': None,
            'final_package': None,
            'reflection_responses': None,
            'ai_agents': None,
        }
        
        # Safely parse JSON fields
        try:
            data['policy_selections'] = json.loads(session.policy_selections) if session.policy_selections else None
        except (json.JSONDecodeError, TypeError):
            pass
            
        try:
            data['final_package'] = json.loads(session.final_package) if session.final_package else None
        except (json.JSONDecodeError, TypeError):
            pass
            
        try:
            data['reflection_responses'] = json.loads(session.reflection_responses) if session.reflection_responses else None
        except (json.JSONDecodeError, TypeError):
            pass
            
        try:
            data['ai_agents'] = json.loads(session.ai_agents) if session.ai_agents else None
        except (json.JSONDecodeError, TypeError):
            pass
        session_data.append(data)
    
    return render_template('admin/player_detail.html',
                         user=user,
                         participant=participant,
                         session_data=session_data)

@admin.route('/download-report/<int:session_id>')
@admin_required
def download_player_report(session_id):
    """Download individual player report"""
    session_obj = GameSession.query.get_or_404(session_id)
    user = User.query.get_or_404(session_obj.user_id)
    participant = Participant.query.filter_by(user_id=user.id).first()
    
    # Generate report content (similar to existing report generation)
    report_content = generate_player_report(user, participant, session_obj)
    
    # Create response with proper headers
    response = make_response(report_content)
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="player_report_{user.username}_{session_id}.md"'
    
    return response

@admin.route('/export-data')
@admin_required
def export_all_data():
    """Export all player data as a ZIP file"""
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Get all users with completed sessions
        users = User.query.join(GameSession).filter(GameSession.current_phase == 'completed').distinct().all()
        
        for user in users:
            sessions = GameSession.query.filter_by(user_id=user.id, current_phase='completed').all()
            participant = Participant.query.filter_by(user_id=user.id).first()
            
            for session in sessions:
                report_content = generate_player_report(user, participant, session)
                filename = f"reports/player_{user.username}_session_{session.id}.md"
                zip_file.writestr(filename, report_content)
    
    zip_buffer.seek(0)
    
    # Create response
    response = make_response(zip_buffer.read())
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename="all_player_reports.zip"'
    
    return response

def generate_player_report(user, participant, session_obj):
    """Generate markdown report for a player session"""
    report_lines = []
    
    # Header
    report_lines.append(f"# Player Report: {user.full_name}")
    report_lines.append(f"**Session ID:** {session_obj.id}")
    report_lines.append(f"**Completed:** {session_obj.completed_at.strftime('%Y-%m-%d %H:%M:%S') if session_obj.completed_at else 'Not completed'}")
    report_lines.append("")
    
    # User information
    report_lines.append("## User Information")
    report_lines.append(f"- **Username:** {user.username}")
    report_lines.append(f"- **Email:** {user.email}")
    report_lines.append(f"- **Created:** {user.created_at.strftime('%Y-%m-%d')}")
    report_lines.append("")
    
    # Participant demographics
    if participant:
        report_lines.append("## Demographics")
        report_lines.append(f"- **Age:** {participant.age}")
        report_lines.append(f"- **Nationality:** {participant.nationality}")
        report_lines.append(f"- **Occupation:** {participant.occupation}")
        report_lines.append(f"- **Education Level:** {participant.education_level}")
        report_lines.append(f"- **Location:** {participant.current_location_city}, {participant.current_location_country}")
        if participant.displacement_experience:
            report_lines.append(f"- **Displacement Experience:** {participant.displacement_experience}")
        report_lines.append("")
    
    # Policy selections
    if session_obj.policy_selections:
        policy_data = json.loads(session_obj.policy_selections)
        report_lines.append("## Policy Selections")
        for area, selection in policy_data.items():
            report_lines.append(f"- **{area.replace('_', ' ').title()}:** {selection}")
        report_lines.append("")
    
    # Final package
    if session_obj.final_package:
        final_data = json.loads(session_obj.final_package)
        report_lines.append("## Final Policy Package")
        for area, selection in final_data.items():
            if area != 'total_cost':
                report_lines.append(f"- **{area.replace('_', ' ').title()}:** {selection}")
        if 'total_cost' in final_data:
            report_lines.append(f"- **Total Cost:** {final_data['total_cost']} units")
        report_lines.append("")
    
    # Reflection responses
    if session_obj.reflection_responses:
        reflection_data = json.loads(session_obj.reflection_responses)
        report_lines.append("## Reflection Responses")
        for question, answer in reflection_data.items():
            report_lines.append(f"**{question}:**")
            report_lines.append(f"{answer}")
            report_lines.append("")
    
    return "\n".join(report_lines)