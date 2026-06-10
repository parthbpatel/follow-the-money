import os

from dotenv import load_dotenv
from ollama import Client

load_dotenv()


def get_ollama_client():
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model_name = os.getenv("OLLAMA_MODEL", "qwen3:4b")

    return Client(host=base_url), model_name
