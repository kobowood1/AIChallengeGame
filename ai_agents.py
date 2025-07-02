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
    Generate a justification for a policy choice based on agent characteristics and conversation context
    
    Args:
        policy_domain (str): The policy area being justified
        option_chosen (int): The option level chosen (1, 2, or 3)
        agent (dict): The agent's demographic and ideological information
        user_message (str, optional): The most recent message from the user
        recent_messages (list, optional): List of recent messages in the conversation
        responding_to_agent (dict, optional): Agent being responded to for agent-to-agent interaction
    
    Returns:
        str: A contextual response to the user's perspective
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
    
    # Construct a prompt for the LLM with more detail and context
    prompt = f"""
    You are {agent['name']}, a {agent['age']}-year-old {agent['occupation']} with a {agent['education_level']} education.
    You identify as {agent['socioeconomic_status']} and have {agent['ideology']} political views.
    
    You're discussing refugee education policy in the Republic of Bean, specifically about {policy_domain}, which involves {policy_description}.
    
    You've chosen option {option_chosen} for this policy area, which is a {option_description}.
    
    {conversation_context}
    
    {interaction_context}
    
    Their message: "{user_message}"
    
    Respond to their message about {policy_domain}. If they asked a question or shared an opinion, address it directly.
    Focus on why you believe option {option_chosen} is the right approach, drawing on your professional experience,
    educational background, socioeconomic perspective, and political ideology.
    
    Be specific and realistic in your response, with concrete examples of how this policy affects your life or community.
    Keep your response concise (3-4 sentences) and conversational in tone.
    Don't mention race, ethnicity, gender, or sexuality. Focus on your occupation, education, economic status, and political views.
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
    
    # Fallback responses - now more conversational
    ideologies = {
        "conservative": "I believe in traditional values and limited government spending.",
        "moderate": "I think balanced approaches usually work best.",
        "liberal": "I support progressive policies that help those in need.",
        "socialist": "I believe in stronger government programs to ensure equality.",
        "neoliberal": "I favor free market solutions with minimal regulation."
    }
    
    option_attitudes = {
        1: "This basic approach is fiscally responsible without overreaching.",
        2: "This middle-ground solution provides a good balance of benefits and costs.",
        3: "This comprehensive approach, while more expensive, addresses the issue properly."
    }
    
    # If we have a user message, acknowledge it in the response
    acknowledgment = ""
    if user_message:
        if responding_to_agent:
            acknowledgment = f"I hear what {responding_to_agent['name']} is saying, but I have a different perspective. "
        else:
            acknowledgment = "I understand your perspective, though I have a different view. "
    
    occupation_relevance = f"As a {agent['occupation']}, I see how this directly affects my work and community."
    
    return f"{acknowledgment}{ideologies.get(agent['ideology'], 'I have well-considered views on this issue.')} {option_attitudes.get(option_chosen, 'This option aligns with my values.')} {occupation_relevance}"