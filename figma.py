""" Mk Utility 3 
    Convert the figma project to tkinter,
    using subprocess and os we call the bash command line and input the token and url and output to the current dir.
"""
import os
import re
import sys
import time
import json
import logging
import subprocess

from datetime import datetime
from pathlib import Path 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    if getattr(sys, 'frozen', False):
        # We are running in a PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # We are running in normal Python environment
        return Path(__file__).parent

PROJECT_ROOT = get_project_root()
sys.path.append(str(PROJECT_ROOT))

# Ensure data directory exists in user's home
DATA_DIR = PROJECT_ROOT / ".figma-converter"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define paths
PATHS = {
    'logs': DATA_DIR / 'logs' / 'app.log',
    'config': DATA_DIR / 'config.json'
}

# Ensure logs directory exists
PATHS['logs'].parent.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(PATHS['logs'])),
        logging.StreamHandler()
    ]
)

logging.info(f"Current project root: {PROJECT_ROOT}")

CONFIG_PATH = PATHS['config']


def create_path():
    try:
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        output_path = DATA_DIR / f"New_gui_{time_stamp}"
        output_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created output directory: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Error occurred while creating path: {e}")
        raise


def convert_url_to_file_format(url):
    """Convert Figma URL to the required format.
    Expected format: https://www.figma.com/file/FILEID
    """
    # Try to extract the file ID from various Figma URL formats
    try:
        if url:
            patterns = [
                r'figma.com/file/([0-9A-Za-z]+)',  # Direct file URL
                r'figma.com/design/([0-9A-Za-z]+)',  # Design URL
            ]
            
            for pattern in patterns:
                if match := re.search(pattern, url):
                    file_id = match.group(1)
                    result = f'https://www.figma.com/file/{file_id}'
                    logging.info(f"Converted URL to format: {result}")
                    return result
        
        raise ValueError("Could not extract Figma file ID from URL")
    except Exception as e:
        logging.error(f"Error while converting the URL pattern: {str(e)}")
        raise

def converter(token, url, path):
    """ using subprocess call the bash command run it to convert to the tkinter
    Command format: tkdesigner [-h] [-o OUTPUT] [-f] file_url token
    """
    
    try:
        # Convert URL to the required format
        file_url = convert_url_to_file_format(url)
        logging.info(f"Converting Figma URL to: {file_url}")
        
        # Correct order: file_url first, then token
        command = f"tkdesigner -o {path} {file_url} {token}"
        logging.debug(f"Running command: {command}")
        
        converter_output = subprocess.run(
            command.split(),  # Split command into list for safer execution
            stderr=subprocess.STDOUT, 
            stdout=subprocess.PIPE, 
            text=True
        )
        logging.info(f"Command output:\n{converter_output.stdout}")
    except subprocess.SubprocessError as e:
        logging.error(f"Error running tkdesigner command: {e}")
        raise

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            # if the json has nothing we need to ensure to return defaul values
            return json.load(f)
    return {}

def save_config(token, url, auto_save='True', theme="light"):
    config = {
        'token': token,
        'url': url,
        'auto_save': auto_save,
        'theme': theme,
        'last_used': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

def get_input(prompt, default=''):
    if default:
        response = input(f"{prompt} (press Enter to use '{default}'): ").strip()
        return response if response else default
    return input(prompt).strip()

def main():
    output_path = create_path()
    logging.info(f"Files will be saved to: {output_path}")
    
    # Load previous configuration if it exists
    config = load_config()
    if config:
        logging.info(f"Found previous configuration from {config.get('last_used', 'unknown date')}")
    
    while True:
        token = get_input("Enter your figma token: ", config.get('token', ''))
        url = get_input("Please enter the url: ", config.get('url', ''))
        
        if token and url:
            logging.info(f"Processing with token: {token[:4]}*** and URL: {url}")
            logging.info("Starting the converter...")
            
            # Save the new configuration
            save_config(token, url)
            
            converter(token, url, output_path)
            break
        else:
            logging.warning("Missing required values. Please enter both token and URL.")
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("System closed by user.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)





