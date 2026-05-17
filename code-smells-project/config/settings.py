import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
DATABASE_URL = os.getenv('DATABASE_URL', 'loja.db')
DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '0.0.0.0')
