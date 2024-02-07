from os import environ
from openai import OpenAI

# get OPENAI_KEY from environment variable
OPENAI_KEY = environ.get('OPENAI_KEY')

def embed_openai(text: str, model='text-embedding-3-small'):
    openai_client = OpenAI(api_key=OPENAI_KEY)
    response = openai_client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding