"""
Voice Engine Module for AI Policy Simulation

This module provides voice synthesis capabilities using OpenAI's Text-to-Speech API.
Each AI agent in the simulation is assigned a unique voice that's used to convert 
their text responses into spoken audio.
"""

import os
import time
import logging
import random
from pathlib import Path
from typing import Dict, Optional, Tuple

import openai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Voice options from OpenAI's TTS API
VOICE_POOL = ["nova", "onyx", "fable", "echo", "shimmer"]

# Keep track of which voice is assigned to which agent
voice_assignments: Dict[str, str] = {}

def ensure_voices_directory():
    """
    Ensure the directory for storing voice files exists.
    """
    voice_dir = Path("static/voices")
    voice_dir.mkdir(parents=True, exist_ok=True)
    return voice_dir

def assign_voice(agent_id: str) -> str:
    """
    Assign a voice to an agent from the voice pool.
    
    Args:
        agent_id: Unique identifier for the agent
        
    Returns:
        The name of the voice assigned to this agent
    """
    # If this agent already has an assigned voice, return it
    if agent_id in voice_assignments:
        return voice_assignments[agent_id]
    
    # If all voices are used, we'll just pick randomly
    if len(voice_assignments) >= len(VOICE_POOL):
        assigned_voice = random.choice(VOICE_POOL)
    else:
        # Find voices that aren't already assigned
        used_voices = set(voice_assignments.values())
        available_voices = [v for v in VOICE_POOL if v not in used_voices]
        assigned_voice = random.choice(available_voices)
    
    # Store the assignment
    voice_assignments[agent_id] = assigned_voice
    logger.info(f"Assigned voice '{assigned_voice}' to agent '{agent_id}'")
    
    return assigned_voice

def generate_agent_voice(text: str, voice: str, filename: str, 
                         retries: int = 3, retry_delay: int = 2) -> Optional[str]:
    """
    Generate speech audio for agent text using OpenAI's TTS API.
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (from VOICE_POOL)
        filename: The filename to save the audio to (must end in .mp3)
        retries: Number of times to retry on failure
        retry_delay: Seconds to wait between retries
        
    Returns:
        The path to the generated audio file, or None if generation failed
    """
    # Ensure we have an API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return None
    
    # Ensure the voices directory exists
    voice_dir = ensure_voices_directory()
    
    # Set up the full file path
    if not filename.endswith(".mp3"):
        filename += ".mp3"
    
    full_path = voice_dir / filename
    
    # Ensure the voice is valid
    if voice not in VOICE_POOL:
        logger.warning(f"Invalid voice '{voice}', using default 'nova'")
        voice = "nova"
    
    # Initialize the OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Try to generate the speech with retries
    attempt = 0
    while attempt < retries:
        try:
            logger.info(f"Generating speech for text: '{text[:50]}...' using voice '{voice}'")
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save the audio file
            with open(full_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Successfully saved audio to {full_path}")
            return str(full_path)
            
        except Exception as e:
            attempt += 1
            logger.error(f"Error generating speech (attempt {attempt}/{retries}): {e}")
            
            if attempt < retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to generate speech after {retries} attempts")
                return None
    
    return None

def generate_justification_audio(agent_id: str, policy_name: str, text: str) -> Tuple[str, Optional[str]]:
    """
    Generate audio for an agent's policy justification.
    
    Args:
        agent_id: The ID of the agent
        policy_name: The name of the policy being justified
        text: The justification text
        
    Returns:
        A tuple of (justification_text, audio_path)
        audio_path will be None if generation failed
    """
    # Get the voice for this agent
    voice = assign_voice(agent_id)
    
    # Create a filename based on the agent and policy
    # Replace spaces with underscores and make lowercase
    safe_policy_name = policy_name.lower().replace(" ", "_")
    filename = f"agent_{agent_id}_{safe_policy_name}.mp3"
    
    # Generate the audio
    audio_path = generate_agent_voice(text, voice, filename)
    
    return (text, audio_path)


# Example usage (can be run directly for testing)
if __name__ == "__main__":
    # This will only run when the module is executed directly
    example_text = "We must invest in teacher training to ensure refugee students receive proper education."
    
    agent_id = "agent1"
    voice = assign_voice(agent_id)
    policy = "Teacher Training"
    
    text, audio_path = generate_justification_audio(agent_id, policy, example_text)
    
    if audio_path:
        print(f"Agent {agent_id} (voice: {voice}): {text}")
        print(f"Audio saved to: {audio_path}")
    else:
        print("Failed to generate audio. Check your API key and internet connection.")