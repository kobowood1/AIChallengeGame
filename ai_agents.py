"""
Module for generating AI agents for policy simulation.
"""
import random
import os
import logging

# Initialize OpenAI client if API key is available
try:
    from openai import OpenAI
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        openai_available = True
    else:
        logging.warning("OpenAI API key not found. Using fallback responses.")
        openai_available = False
except ImportError:
    logging.warning("OpenAI package not installed. Using fallback responses.")
    openai_available = False

# Initialize Google Gemini client if API key is available
try:
    import google.generativeai as genai
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_available = True
    else:
        logging.warning("Gemini API key not found. Using fallback responses.")
        gemini_available = False
except ImportError:
    logging.warning("Google Generative AI package not installed. Using fallback responses.")
    gemini_available = False

def generate_agents():
    """
    Generate a diverse set of four agents with different characteristics
    
    Returns:
        list: Four agent dictionaries with demographic and ideological information
    """
    # Define possible values for agent attributes
    names = [
        "Alex Johnson", "Sam Rivera", "Jordan Chen", "Taylor Smith", 
        "Morgan Lee", "Casey Wilson", "Riley Martinez", "Jamie Garcia",
        "Drew Thompson", "Quinn Murphy", "Avery Anderson", "Jordan Evans"
    ]
    
    age_ranges = [(25, 35), (36, 45), (46, 55), (56, 75)]
    
    occupations = [
        "Teacher", "Software Engineer", "Small Business Owner", "Nurse", 
        "Construction Worker", "Accountant", "Chef", "Retail Manager",
        "Farmer", "Truck Driver", "Office Administrator", "Electrician",
        "Lawyer", "Factory Worker", "Customer Service Representative", "Sales Representative"
    ]
    
    education_levels = [
        "High School", "Associate's Degree", "Bachelor's Degree", "Master's Degree", 
        "Doctoral Degree", "Trade School", "Some College"
    ]
    
    socioeconomic_statuses = ["Working Class", "Middle Class", "Upper Middle Class", "Wealthy"]
    
    ideologies = ["conservative", "moderate", "liberal", "socialist", "neoliberal"]
    
    # Create four agents with different characteristics
    agents = []
    used_names = set()
    used_occupations = set()
    
    # Assign LLM models: first 2 agents use OpenAI, last 2 use Gemini
    llm_assignments = ["openai", "openai", "gemini", "gemini"]
    
    for i in range(4):
        # Ensure diversity by selecting different demographic features
        while True:
            name = random.choice(names)
            if name not in used_names:
                used_names.add(name)
                break
        
        age_range = age_ranges[i]
        age = random.randint(age_range[0], age_range[1])
        
        while True:
            occupation = random.choice(occupations)
            if occupation not in used_occupations:
                used_occupations.add(occupation)
                break
        
        education = random.choice(education_levels)
        socioeconomic = random.choice(socioeconomic_statuses)
        ideology = random.choice(ideologies)
        
        agent = {
            "name": name,
            "age": age,
            "occupation": occupation,
            "education_level": education,
            "socioeconomic_status": socioeconomic,
            "ideology": ideology,
            "llm_model": llm_assignments[i]
        }
        
        agents.append(agent)
    
    return agents

def agent_justify(policy_domain, option_chosen, agent, user_message='', recent_messages=None, responding_to_agent=None):
    """
    Generate an interactive, engaging response based on agent characteristics and conversation context
    
    Args:
        policy_domain (str): The policy area being justified
        option_chosen (int): The option level chosen (1, 2, or 3)
        agent (dict): The agent's demographic and ideological information
        user_message (str, optional): The most recent message from the user
        recent_messages (list, optional): List of recent messages in the conversation
        responding_to_agent (dict, optional): Agent being responded to for agent-to-agent interaction
    
    Returns:
        str: An interactive response with agreement/disagreement and follow-up questions
    """
    if recent_messages is None:
        recent_messages = []
    
    # Get the LLM model for this agent (default to OpenAI if not specified)
    agent_llm = agent.get('llm_model', 'openai')
    
    # Format recent conversation history for context
    conversation_context = ""
    if recent_messages:
        conversation_context = "Recent conversation:\n"
        for msg in recent_messages:
            sender = msg.get('sender', 'Unknown')
            message = msg.get('message', '')
            conversation_context += f"{sender}: {message}\n"
    
    # Get specific policy domain knowledge
    policy_descriptions = {
        "Language Support": "Programs to help refugee students learn the host country language",
        "Teacher Training": "Preparing teachers to work effectively with refugee students",
        "School Integration": "Measures to incorporate refugee students into mainstream schools",
        "Psychosocial Support": "Mental health services for refugee students dealing with trauma",
        "Curriculum Adaptation": "Modifying educational content to be accessible and relevant to refugee students",
        "Access to Education": "Ensuring refugee students can physically attend and enroll in schools",
        "Certification & Accreditation": "Recognizing refugees' prior education and helping them gain credentials",
        "Financial Support": "Providing monetary assistance for refugee students' educational needs",
        "Language Instruction": "Teaching host country language to refugee students"
    }
    
    option_descriptions = {
        1: "basic approach (lower cost, minimal intervention)",
        2: "moderate approach (balanced cost and intervention)",
        3: "comprehensive approach (higher cost, maximum intervention)"
    }
    
    policy_description = policy_descriptions.get(policy_domain, "policy area related to refugee education")
    option_description = option_descriptions.get(option_chosen, "approach")
    
    # Determine interaction type and adjust prompt accordingly
    interaction_context = ""
    if responding_to_agent:
        interaction_context = f"You are responding to {responding_to_agent['name']}, another policy advisor who just shared their perspective."
    elif user_message:
        interaction_context = "You are responding to the human policy advisor who just shared their perspective."
    
    # Create diverse personality-driven prompts
    personality_traits = {
        'conservative': 'cautious, practical, focused on proven solutions and fiscal responsibility',
        'moderate': 'balanced, diplomatic, seeking middle-ground solutions',
        'liberal': 'progressive, idealistic, prioritizing equity and comprehensive support',
        'humanitarian': 'compassionate, student-focused, emphasizing human dignity and wellbeing',
        'socialist': 'systemic, collective-focused, emphasizing structural change'
    }
    
    speaking_styles = {
        'conservative': 'speak directly and matter-of-factly, often citing practical concerns',
        'moderate': 'speak thoughtfully and diplomatically, acknowledging multiple perspectives',
        'liberal': 'speak passionately about social justice, using inclusive language',
        'humanitarian': 'speak with empathy and personal anecdotes, focusing on individual impact',
        'socialist': 'speak analytically about systems and collective solutions'
    }
    
    agent_personality = personality_traits.get(agent['ideology'], 'thoughtful and professional')
    agent_style = speaking_styles.get(agent['ideology'], 'speak clearly and professionally')
    
    # Enhanced prompt for interactive engagement
    prompt = f"""
    You are {agent['name']}, a {agent['age']}-year-old {agent['occupation']} with a {agent['education_level']} education.
    You identify as {agent['socioeconomic_status']} and have {agent['ideology']} political views.
    
    Your personality is {agent_personality}. When you speak, you {agent_style}.
    
    You're in a policy deliberation about refugee education in the Republic of Bean, discussing {policy_domain}.
    
    CONVERSATION CONTEXT:
    {conversation_context}
    {interaction_context}
    
    Recent message: "{user_message}"
    
    RESPONSE REQUIREMENTS:
    1. FIRST: State your own policy choice clearly: "I support Option {option_chosen} for {policy_domain} because..."
    2. THEN: Only if there's an actual previous message, respond to it with agreement/disagreement  
    3. Give your reasoning based on your {agent['ideology']} worldview and {agent['occupation']} experience  
    4. Reference specific aspects of option {option_chosen} for {policy_domain}
    5. End with a follow-up question that advances the discussion
    6. Keep response 2-3 sentences, be direct and engaging
    
    EXAMPLES OF STRONG OPENINGS:
    - "I support Option {option_chosen} because [your reasoning]. If someone made a previous point, I agree/disagree because..."
    - "My preference is Option {option_chosen} given [your reasoning]. The previous comment raises good points about..."  
    - "I favor Option {option_chosen} from my experience as a {agent['occupation']}. To build on what was said..."
    - "Option {option_chosen} makes the most sense to me because [reasoning]. I have a different perspective on what was mentioned..."
    
    Make this feel like a real policy debate where people challenge each other's ideas!
    """
    
    try:
        if agent_llm == 'gemini' and gemini_available:
            # Use Gemini
            response = gemini_model.generate_content(
                f"You generate brief, realistic responses from simulated citizens who respond to others' perspectives while explaining their policy preferences. You focus on creating believable dialogue that reflects how real people with diverse backgrounds discuss policy issues.\n\n{prompt}",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.7,
                )
            )
            justification = response.text.strip()
            return justification
        elif agent_llm == 'openai' and openai_available:
            # Use OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You generate brief, realistic responses from simulated citizens who respond to others' perspectives while explaining their policy preferences. You focus on creating believable dialogue that reflects how real people with diverse backgrounds discuss policy issues."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            justification = response.choices[0].message.content.strip()
            return justification
    except Exception as e:
        logging.error(f"Error using {agent_llm} API for agent {agent['name']}: {e}")
        # Fall through to fallback response
    
    # Diverse fallback responses if no API is available
    diverse_responses = {
        ("conservative", 1): "As a fiscal conservative, I picked Option 1 because we need to prove programs work before expanding them.",
        ("conservative", 2): "Option 2 makes financial sense - it's substantial enough to help without breaking the budget.",
        ("conservative", 3): "Though costly, Option 3 could save money long-term by preventing bigger social problems.",
        
        ("moderate", 1): "Option 1 is a sensible starting point - we can always expand successful programs later.",
        ("moderate", 2): "I chose Option 2 because it addresses key needs while remaining politically feasible.",
        ("moderate", 3): "Option 3 represents the bold investment these students deserve, despite the higher cost.",
        
        ("liberal", 1): "While I'd prefer more, Option 1 at least establishes the principle that we must help.",
        ("liberal", 2): "Option 2 provides meaningful support that could transform these students' lives.",
        ("liberal", 3): "Option 3 is the only ethical choice - anything less fails our moral obligations.",
        
        ("humanitarian", 1): "Option 1 focuses on immediate needs - sometimes simple solutions work best.",
        ("humanitarian", 2): "Option 2 addresses the whole child, not just academic needs.",
        ("humanitarian", 3): "These students have suffered enough - Option 3 gives them what they truly need.",
        
        ("socialist", 1): "Option 1 is a first step toward systemic change in how we support marginalized students.",
        ("socialist", 2): "Option 2 shows we're serious about addressing structural inequalities in education.",
        ("socialist", 3): "Option 3 represents the kind of comprehensive support that transforms society."
    }
    
    # If we have a user message, acknowledge it in the response
    acknowledgment = ""
    if user_message:
        if responding_to_agent:
            acknowledgment = f"I hear what {responding_to_agent['name']} is saying, but I disagree. "
        else:
            acknowledgment = "I understand your point, though I see it differently. "
    
    ideology_key = agent['ideology'].lower()
    response_key = (ideology_key, option_chosen)
    
    base_response = diverse_responses.get(response_key, f"I chose Option {option_chosen} based on my experience and values.")
    
    return f"{acknowledgment}{base_response}"