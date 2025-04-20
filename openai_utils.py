"""
Utility functions for interacting with OpenAI API.
"""
import os
import json
import logging
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def generate_policy_profile(player_package, final_package, participant_info=None):
    """
    Generate a profile description of the user based on their policy choices.
    
    Args:
        player_package (dict): The user's initial policy selections
        final_package (dict): The final approved policy package
        participant_info (dict, optional): Basic participant information
        
    Returns:
        str: A descriptive paragraph about the user based on their policy choices
    """
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing. Cannot generate policy profile.")
        return "Unable to generate a policy profile. OpenAI API key is missing."
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Create a text description of the policy choices
        policy_description = "Initial policy selections:\n"
        for policy_name, option_level in player_package.items():
            policy_description += f"- {policy_name}: Option {option_level}\n"
        
        policy_description += "\nFinal approved package:\n"
        for policy_name, option_level in final_package.items():
            initial_option = player_package.get(policy_name, "N/A")
            if initial_option != option_level:
                policy_description += f"- {policy_name}: Option {option_level} (changed from {initial_option})\n"
            else:
                policy_description += f"- {policy_name}: Option {option_level}\n"
        
        # Add participant info if available
        if participant_info:
            policy_description += "\nParticipant information:\n"
            for key, value in participant_info.items():
                policy_description += f"- {key}: {value}\n"
        
        # Prepare prompt for OpenAI
        prompt = f"""
        Based on the following policy selections for the Republic of Bean refugee education policy simulation, 
        create a 1-paragraph profile (approximately 100-150 words) of the policymaker. 
        
        Focus on their values, priorities, and approach to refugee education policy based on these choices.
        Analyze the balance between immediate humanitarian needs and long-term integration,
        as well as their approach to resource allocation given budget constraints.
        Consider their apparent ideological leanings based on their policy preferences.
        
        {policy_description}
        
        Remember to:
        - Write in third person
        - Be descriptive but concise
        - Avoid judgment or explicitly stating political affiliation
        - Maintain a thoughtful, analytical tone
        """
        
        # Call OpenAI API - the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert political analyst specializing in education policy and refugee integration."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        
        # Extract the generated profile
        profile = response.choices[0].message.content.strip()
        logger.info("Successfully generated policy profile using OpenAI")
        
        return profile
        
    except Exception as e:
        logger.error(f"Failed to generate profile using OpenAI: {str(e)}")
        return f"Unable to generate a policy profile at this time due to a technical issue: {str(e)}"