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

def agent_justify(policy_domain, option_chosen, agent):
    """
    Generate a justification for a policy choice based on agent characteristics
    
    Args:
        policy_domain (str): The policy area being justified
        option_chosen (int): The option level chosen (1, 2, or 3)
        agent (dict): The agent's demographic and ideological information
    
    Returns:
        str: A three-sentence justification for the policy choice
    """
    # Check if OpenAI is available
    if 'openai_available' in globals() and openai_available:
        try:
            # Construct a prompt for the OpenAI API
            prompt = f"""
            You are {agent['name']}, a {agent['age']}-year-old {agent['occupation']} with a {agent['education_level']} education.
            You identify as {agent['socioeconomic_status']} and have {agent['ideology']} political views.
            
            You've chosen option {option_chosen} for {policy_domain} policy.
            
            Provide a three-sentence justification for this policy choice that reflects your background and ideology.
            Don't mention race, ethnicity, gender, or sexuality. Focus on your occupation, education, economic status, and political views.
            Make your response exactly three sentences - no more, no less.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You generate brief, realistic responses from simulated citizens explaining their policy preferences."},
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
    
    # Fallback responses
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
    
    occupation_relevance = f"As a {agent['occupation']}, I see how this directly affects my work and community."
    
    return f"{ideologies.get(agent['ideology'], 'I have well-considered views on this issue.')} {option_attitudes.get(option_chosen, 'This option aligns with my values.')} {occupation_relevance}"