import httpx
import urllib.parse
import asyncio
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import os

load_dotenv()

async def test_hf():
    client = InferenceClient(

provider="replicate",
        api_key=os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN"),
    )
    
    print("Generating...")
    try:
        # run synchronous call in a thread to prevent blocking
        image = await asyncio.to_thread(
            client.text_to_image,
            "A cute kitten",
            model="black-forest-labs/FLUX.1-dev",
        )
        print("Success! Image type:", type(image))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_hf())
