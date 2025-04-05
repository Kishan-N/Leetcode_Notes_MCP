import os
from pathlib import Path
import json

CONFIG_FILE = 'config.json'

def load_api_key():
    """Load OpenAI API key from config file."""
    config_path = Path(CONFIG_FILE)
    
    # If config file exists, load key from it
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('OPENAI_API_KEY')
        except:
            pass
    
    # If no key found, prompt user
    print("\nOpenAI API key not found. Please enter your API key:")
    api_key = input("> ").strip()
    
    # Save to config file
    with open(config_path, 'w') as f:
        json.dump({'OPENAI_API_KEY': api_key}, f)
    
    return api_key

def save_api_key(api_key: str):
    """Save OpenAI API key to config file."""
    config_path = Path(CONFIG_FILE)
    with open(config_path, 'w') as f:
        json.dump({'OPENAI_API_KEY': api_key}, f)

def update_api_key():
    """Update the OpenAI API key."""
    print("\nEnter new OpenAI API key:")
    api_key = input("> ").strip()
    save_api_key(api_key)
    return api_key 