# The CHALLENGE: Policy Jam - Refugee Edition

A dynamic, AI-powered collaborative policy-making simulation platform designed to transform complex decision-making into an engaging, interactive learning experience through advanced technological integrations.

## 📋 Project Overview

This web application simulates the policy-making process for refugee education in the fictional "Republic of Bean." It allows users to:

1. Make education policy decisions within budget constraints
2. Interact with AI agents representing diverse ideological perspectives
3. Engage in collaborative deliberation and voting processes
4. Reflect on their decision-making experience
5. Receive AI-generated policy profile analysis based on their choices
6. Get detailed reports emailed to research teams

The simulation unfolds over three distinct phases:
- **Phase 1:** Individual policy selection within budget constraints
- **Phase 2:** Group deliberation with AI agents and voting
- **Phase 3:** Reflection and reporting

## 🚀 Features

- **Multi-phase Interactive Experience**: Progressive gameplay that mimics real policy deliberation
- **AI-Powered Agents**: Four ideologically diverse AI agents that provide realistic perspectives and debate policy options
- **Dynamic Deliberation**: Live conversation interface for debating policies with AI agents
- **Budget Constraints**: Limited resources force strategic trade-offs between competing worthy goals
- **Gamified Interface**:
  - Animated budget depletion notifications
  - Color-coded policy options with intuitive icons
  - Visual budget tracking with dynamic color changes
  - Interactive UI elements with micro-animations
- **Voting System**: Democratic majority-rule process with random tiebreaker
- **Policy Profiling**: AI-generated analysis of user policy choices and reasoning
- **Reflection Framework**: Guided questions for deep reflection on the simulation experience
- **Report Generation**: Comprehensive reports in Markdown format
- **Email Integration**: Automated email delivery of reports to research teams
- **Database Storage**: Persistent data capture of participant information and choices

## 💻 Technical Stack

### Backend
- **Flask**: Web framework for the application core
- **Flask-SocketIO**: Real-time communication for interactive deliberation
- **Flask-SQLAlchemy**: ORM for database operations
- **Flask-WTF**: Form validation and CSRF protection
- **Gunicorn/Eventlet**: WSGI server with async support

### Frontend
- **HTML/CSS/JavaScript**: Core web technologies
- **Tailwind CSS**: Responsive, modern design framework
- **Font Awesome**: Comprehensive icon library for enhanced UI
- **Socket.IO (client)**: Real-time communication
- **CSS Animations**: Micro-interactions and visual feedback

### AI Integration
- **OpenAI API**: Powers the AI agents and policy profile generation
  - GPT-4o: Used for dynamic agent responses and content generation
  - Contextual processing: Agents respond to specific deliberation topics

### Data Processing & Delivery
- **SendGrid API**: Email service for report distribution
- **Markdown**: Used for report formatting
- **WeasyPrint**: PDF generation (optional)

### Database
- **PostgreSQL**: Relational database for participant information

## 🏛️ Architecture

The application follows a modular architecture with clear separation of concerns:

- **app.py**: Application factory and core configuration
- **routes.py**: HTTP routes for page rendering and form handling
- **models.py**: Database models for participant information
- **game.py**: Game mechanics and session management
- **events.py**: Socket.IO event handlers for real-time communication
- **game_data.py**: Policy information and budget validation
- **ai_agents.py**: AI agent generation and response handling
- **challenge_content.py**: Scenario content and policy areas
- **email_utils.py**: Email functionality via SendGrid
- **openai_utils.py**: OpenAI API integration and policy profile generation

## 🔧 Setup & Configuration

### Prerequisites
- Python 3.11+
- PostgreSQL database
- SendGrid API key
- OpenAI API key

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SENDGRID_API_KEY`: SendGrid API key for email sending
- `OPENAI_API_KEY`: OpenAI API key for AI feature functionality

### Installation & Running
1. Install Python dependencies: `pip install -r requirements.txt`
2. Set up environment variables (see above)
3. Start the application: `gunicorn --bind 0.0.0.0:5000 --worker-class eventlet main:app`

## 🎮 Simulation Flow

1. **Registration**: Participants provide demographic information
2. **Scenario Introduction**: Background on the Republic of Bean's refugee situation
3. **Phase 1 - Selection**: 
   - Choose policy options within budget constraints
   - Interactive visual feedback for budget utilization
   - Budget depletion notifications
   - Color-coded options with clear cost indicators
4. **Phase 2 - Deliberation**: 
   - Real-time discussion with AI agents
   - Spontaneous debates between AI agents
   - Voting mechanism with visual results
5. **Phase 3 - Reflection**: 
   - Answer reflection questions
   - Receive AI-generated policy profile
6. **Thank You Page**: Download report and confirmation of email delivery

## 🎲 Gamification Elements

The application incorporates several gamification elements to enhance user engagement:
- **Budget Management**: Resource allocation with dynamic visual feedback
- **Interactive UI**: Animations, micro-interactions, and visual transitions
- **Color Psychology**: Semantic colors for different option levels (blue for basic, purple for moderate, red for comprehensive)
- **Feedback Mechanisms**: Pop-up notifications for important events like budget depletion
- **Strategic Choices**: Decisions with meaningful trade-offs and clear visual representation
- **Progress Indicators**: Visual feedback showing advancement through the simulation
- **Engaging Terminology**: Using terms like "mission," "policy points," and "levels" to create a game-like experience

## 🤖 AI Agent Design

The simulation includes four AI agents with diverse ideological perspectives:
- Each agent has specific demographic and ideological attributes
- Agents provide contextual responses based on their characteristics
- Agents can spontaneously debate with each other after user messages
- Agent names are prefixed with "AI-" to distinguish them from human players

## 📧 Email Functionality

- Uses SendGrid API for email delivery
- Requires a verified sender email in production mode
- Sends reports to designated recipients
- Reports include participant info, policy selections, and reflection responses
- Reports are formatted in Markdown with policy profile analysis

## 🔍 Data Collection

The platform collects:
- Participant demographics (age, nationality, occupation, education level, location)
- Policy selections and budget allocation
- Deliberation outcomes and voting results
- Reflection responses to prompted questions

## 📈 Future Enhancements

Potential areas for future development:
- Voice to text and text to Voice features
- Multiple scenario support for different policy domains
- Enhanced visualization of policy impacts
- Advanced analytics dashboard for researchers
- Integration with learning management systems
- Support for larger deliberation groups
- Integration with real-world policy databases

## 📝 License

Copyright © 2025 The CHALLENGE: Policy Jam - Refugee Edition
