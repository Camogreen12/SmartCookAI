import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv('OPENAI_API_KEY')

# Database Configuration
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "smartchef.db"

# Flask Configuration
SECRET_KEY = os.urandom(24).hex()
DEBUG = True

# AI Model Configuration
AI_MODEL = "gpt-4"
MAX_TOKENS = 1000
TEMPERATURE = 0.7 