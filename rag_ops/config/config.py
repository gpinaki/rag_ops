import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "./data/vectorstore")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1500))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
