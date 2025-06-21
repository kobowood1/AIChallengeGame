# The CHALLENGE: Policy Jam - Refugee Edition

## Overview

This is a Flask-based web application that simulates policy-making processes for refugee education in the fictional "Republic of Bean." The application combines AI-powered agents, real-time deliberation, gamification elements, and educational assessment to create an immersive policy simulation experience. Users progress through three distinct phases: individual policy selection, group deliberation with AI agents, and reflective analysis.

## System Architecture

### Backend Architecture
- **Flask Web Framework**: Core application server with Blueprint-based route organization
- **Flask-SocketIO**: Real-time bidirectional communication for live deliberation sessions
- **Flask-Login**: User authentication and session management
- **Flask-WTF**: Form handling with CSRF protection
- **SQLAlchemy ORM**: Database abstraction layer for PostgreSQL
- **Gunicorn + Eventlet**: Production WSGI server with async WebSocket support

### Frontend Architecture
- **Server-Side Rendered Templates**: Jinja2 templating with responsive HTML
- **Tailwind CSS**: Utility-first CSS framework for modern, responsive design
- **Vanilla JavaScript**: Client-side interactivity without heavy frameworks
- **Socket.IO Client**: Real-time communication for deliberation features

### Database Design
- **PostgreSQL**: Primary data store configured via environment variables
- **User Management**: Authentication, profiles, and session tracking
- **Game State**: Participant information, policy selections, and game sessions
- **Audit Trail**: Complete capture of user interactions and decision flows

## Key Components

### Authentication System
- User registration and login with secure password hashing
- Session-based authentication with Flask-Login
- CSRF protection on all forms
- User dashboard with game state management

### Game Logic Engine (`game.py`, `game_data.py`)
- Multi-phase game progression with state management
- Budget constraint validation (14-unit maximum)
- Policy option selection with cost calculations
- AI agent generation with diverse characteristics

### AI Integration
- **OpenAI API Integration**: Policy profile generation and agent responses
- **AI Agent System**: Four diverse agents with different ideological perspectives
- **Fallback Mechanisms**: Graceful degradation when AI services unavailable

### Real-Time Deliberation
- **Socket.IO Events**: Live policy discussion between human and AI participants
- **Room Management**: Isolated deliberation sessions with unique identifiers
- **State Synchronization**: Real-time updates across all participants

### Email Reporting System
- **SendGrid Integration**: Automated report delivery to research teams
- **Markdown Reports**: Structured policy analysis and participant insights
- **PDF Generation**: WeasyPrint for formatted document output

### Policy Content Management
- **Structured Policy Data**: Seven policy areas with three options each
- **Budget Validation**: Real-time cost tracking and constraint enforcement
- **Content Modularity**: Separation of game content from application logic

## Data Flow

### User Journey
1. **Registration/Login**: User authentication and demographic collection
2. **Scenario Introduction**: Background context and mission briefing
3. **Phase 1**: Individual policy selection within budget constraints
4. **Phase 2**: Group deliberation with AI agents and voting
5. **Phase 3**: Reflection, profiling, and report generation

### Policy Selection Flow
- User selects one option from each of seven policy areas
- Real-time budget tracking prevents exceeding 14-unit limit
- Validation ensures diverse option selection (mix of cost levels)
- Selections stored in database with participant context

### Deliberation Process
- WebSocket connection established for real-time communication
- AI agents present diverse perspectives on policy choices
- Democratic voting process with majority rule and random tie-breaking
- Final policy package determined through group consensus

### Report Generation
- AI-generated policy profile based on user selections and reasoning
- Comprehensive reflection analysis with guided questions
- Automated email delivery to research team recipients
- Persistent storage of all participant data and insights

## External Dependencies

### Required Services
- **PostgreSQL Database**: User data, game sessions, and policy selections
- **OpenAI API**: AI agent responses and policy profile generation
- **SendGrid Email API**: Automated report delivery system

### Python Packages
- Flask ecosystem (Flask, Flask-SocketIO, Flask-Login, Flask-WTF, Flask-SQLAlchemy)
- Database: psycopg2-binary for PostgreSQL connectivity
- AI: openai package for API integration
- Email: sendgrid for email delivery
- PDF: weasyprint for document generation
- Server: gunicorn with eventlet for production deployment

### Frontend Libraries
- Tailwind CSS via CDN for responsive styling
- Socket.IO client for real-time communication
- Font Awesome for iconography

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with PostgreSQL 16
- **Environment**: Nix package manager with stable-24_05 channel
- **Server**: Gunicorn with eventlet worker for WebSocket support
- **Ports**: 5000 (main app), 5001 (alternative)

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API authentication
- `SENDGRID_API_KEY`: Email service authentication
- `SESSION_SECRET`: Flask session encryption key

### Production Considerations
- Autoscale deployment target for variable load
- Connection pooling with pre-ping for database reliability
- Graceful degradation when external services unavailable
- Comprehensive error logging and monitoring

## Recent Changes

✓ Implemented card-playing simulation interface with 15 interactive policy cards
✓ Added authentic custom card images for Language Instruction, Teacher Training, and Curriculum Adaptation
✓ Optimized card sizing to 320px width for perfect three-column desktop layout
✓ Applied full-resolution image display without container constraints using CSS Grid
✓ Added responsive breakpoints for tablet (2 columns) and mobile (1 column) layouts

## Changelog
- June 21, 2025. Initial setup and card interface implementation

## User Preferences

Preferred communication style: Simple, everyday language.