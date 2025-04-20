"""
Module for generating AI agents for policy simulation.
"""
import random
import os
import logging

# Initialize OpenAI client if API key is available
try:
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        openai_available = True
    else:
        logging.warning("OpenAI API key not found. Using fallback responses.")
        openai_available = False
except ImportError:
    logging.warning("OpenAI package not installed. Using fallback responses.")
    openai_available = False

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
            "ideology": ideology
        }
        
        agents.append(agent)
    
    return agents

def agent_justify(policy_domain, option_chosen, agent, user_message='', recent_messages=None):
    """
    Generate a justification for a policy choice based on agent characteristics and conversation context
    
    Args:
        policy_domain (str): The policy area being justified
        option_chosen (int): The option level chosen (1, 2, or 3)
        agent (dict): The agent's demographic and ideological information
        user_message (str, optional): The most recent message from the user
        recent_messages (list, optional): List of recent messages in the conversation
    
    Returns:
        str: A contextual response to the user's perspective
    """
    if recent_messages is None:
        recent_messages = []
    
    # Check if OpenAI is available
    if 'openai_available' in globals() and openai_available:
        try:
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
            
            # Construct a prompt for the OpenAI API with more detail and context
            prompt = f"""
            You are {agent['name']}, a {agent['age']}-year-old {agent['occupation']} with a {agent['education_level']} education.
            You identify as {agent['socioeconomic_status']} and have {agent['ideology']} political views.
            
            You're discussing refugee education policy in the Republic of Bean, specifically about {policy_domain}, which involves {policy_description}.
            
            You've chosen option {option_chosen} for this policy area, which is a {option_description}.
            
            {conversation_context}
            
            The user just shared their perspective: "{user_message}"
            
            Respond to the user's message about {policy_domain}. If they asked a question or shared an opinion, address it directly.
            Focus on why you believe option {option_chosen} is the right approach, drawing on your professional experience,
            educational background, socioeconomic perspective, and political ideology.
            
            Be specific and realistic in your response, with concrete examples of how this policy affects your life or community.
            Keep your response concise (3-4 sentences) and conversational in tone.
            Don't mention race, ethnicity, gender, or sexuality. Focus on your occupation, education, economic status, and political views.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
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
            logging.error(f"Error using OpenAI API: {e}")
            # Fall through to the fallback response
    
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
        acknowledgment = "I understand your perspective, though I have a different view. "
    
    occupation_relevance = f"As a {agent['occupation']}, I see how this directly affects my work and community."
    
    return f"{acknowledgment}{ideologies.get(agent['ideology'], 'I have well-considered views on this issue.')} {option_attitudes.get(option_chosen, 'This option aligns with my values.')} {occupation_relevance}"