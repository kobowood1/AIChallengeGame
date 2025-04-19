"""
Test script to verify voice_engine module functionality.
"""

import os
import logging
from voice_engine import assign_voice, generate_agent_voice, ensure_voices_directory

logging.basicConfig(level=logging.INFO)

def test_voice_engine():
    """Test the voice engine functionality."""
    print("Testing voice engine module...")
    
    # Ensure voices directory exists
    voices_dir = ensure_voices_directory()
    print(f"Voices directory: {voices_dir}")
    
    # Assign a voice
    agent_id = "test_agent"
    voice = assign_voice(agent_id)
    print(f"Assigned voice '{voice}' to agent '{agent_id}'")
    
    # Generate a test audio file
    test_text = "This is a test of the voice synthesis system for the Republic of Bean policy simulation."
    filename = "test_audio.mp3"
    
    audio_path = generate_agent_voice(test_text, voice, filename)
    
    if audio_path:
        print(f"Successfully generated audio at: {audio_path}")
        file_size = os.path.getsize(audio_path)
        print(f"Audio file size: {file_size} bytes")
    else:
        print("Failed to generate audio.")
    
    return audio_path is not None

if __name__ == "__main__":
    if test_voice_engine():
        print("Voice engine test completed successfully!")
    else:
        print("Voice engine test failed.")