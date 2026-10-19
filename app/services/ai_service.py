# # backend/app/services/ai_service.py
# import os
# import base64
# import json
# from groq import Groq

# def get_groq_client() -> Groq:
#     """Lazy-loads the Groq client, safely ignoring system proxy variables."""
#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise RuntimeError("GROQ_API_KEY is not configured. Add it to the backend .env file.")
    
#     # SAFEGUARD: Clear proxy environment variables to prevent the 
#     # "unexpected keyword argument 'proxies'" bug in the Groq client.
#     os.environ.pop("HTTP_PROXY", None)
#     os.environ.pop("HTTPS_PROXY", None)
#     os.environ.pop("http_proxy", None)
#     os.environ.pop("https_proxy", None)
    
#     return Groq(api_key=api_key)

# def get_image_description(image_url_path: str) -> str:
#     """Uses Groq Vision to analyze the image and return a text description."""
#     try:
#         client = get_groq_client()
#         local_file_path = image_url_path.lstrip("/")
        
#         with open(local_file_path, "rb") as f:
#             base64_image = base64.b64encode(f.read()).decode('utf-8')

#         # Using the currently supported Llama 3.2 11B Vision model
#         chat_completion = client.chat.completions.create(
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": "Describe this pet photo in detail. What is the pet doing, what is the setting, and what is the overall mood?"},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/webp;base64,{base64_image}",
#                             },
#                         },
#                     ],
#                 }
#             ],
#             model="qwen/qwen3.6-27b",
#         )
#         return chat_completion.choices[0].message.content
#     except Exception as e:
#         print(f"Groq Vision Error (Fallback triggered): {e}")
#         return "A photo of a pet."

# def generate_memory_story(pet_name: str, image_description: str, user_note: str = "") -> dict:
#     """Uses Groq LLM to generate a heartwarming story and structured JSON tags."""
#     try:
#         client = get_groq_client()
        
#         # Ensure inputs are strictly strings to prevent "content must be a string" errors
#         pet_name_str = str(pet_name) if pet_name else "Pet"
#         desc_str = str(image_description) if image_description else "A photo."
#         note_str = str(user_note) if user_note else ""

#         prompt = f"""
#         You are the 'AI Memory Editor' for a pet app called TAILSTORY. 
#         Your job is to turn raw moments into beautiful, emotional memories.

#         Pet's Name: {pet_name_str}
#         Photo Description: {desc_str}
#         Owner's Note: "{note_str}"

#         Your task:
#         1. Write a beautiful, heartwarming 2-3 sentence story about this specific memory.
#         2. Extract structured metadata.

#         Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
#         {{
#             "story": "The heartwarming story here.",
#             "tags": {{
#                 "objects": ["object1", "object2"],
#                 "mood": "happy",
#                 "setting": "beach"
#             }}
#         }}
#         """
        
#         # Using the currently supported Llama 3.1 70B Versatile model for reliable JSON
#         chat_completion = client.chat.completions.create(
#             messages=[{"role": "user", "content": prompt}],
#             model="openai/gpt-oss-120b",
#             response_format={"type": "json_object"}
#         )
        
#         # Parse the JSON string returned by the model
#         result_text = chat_completion.choices[0].message.content
#         return json.loads(result_text)
        
#     except Exception as e:
#         print(f"Groq Story Generation Error (Fallback triggered): {e}")
#         # Graceful fallback if AI fails or key is missing
#         return {
#             "story": user_note or f"A wonderful memory with {pet_name}.",
#             "tags": {"objects": [], "mood": "unknown", "setting": "unknown"}
#         }

# backend/app/services/ai_service.py
import os
import base64
import json
from groq import Groq

def get_groq_client() -> Groq:
    """Lazy-loads the Groq client, safely ignoring system proxy variables."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured. Add it to the backend .env file.")
    
    # SAFEGUARD: Clear proxy environment variables to prevent client initialization bugs
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)
    
    return Groq(api_key=api_key)

def get_image_description(image_url_path: str) -> str:
    """Uses Groq Vision to analyze the image and return a text description."""
    try:
        client = get_groq_client()
        local_file_path = image_url_path.lstrip("/")
        
        with open(local_file_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this pet photo in detail. What is the pet doing, what is the setting, and what is the overall mood?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/webp;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="qwen/qwen3.6-27b", # Active free-tier vision model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq Vision Error: {e}")
        raise e # Re-raise so the router catches it and logs it

def generate_memory_story(pet_name: str, image_description: str, user_note: str = "") -> dict:
    """Uses Groq LLM to generate a heartwarming story and structured JSON tags."""
    try:
        client = get_groq_client()
        
        pet_name_str = str(pet_name) if pet_name else "Pet"
        desc_str = str(image_description) if image_description else "A photo."
        note_str = str(user_note) if user_note else ""

        prompt = f"""
        You are the 'AI Memory Editor' for a pet app called TAILSTORY. 
        Your job is to turn raw moments into beautiful, emotional memories.

        Pet's Name: {pet_name_str}
        Photo Description: {desc_str}
        Owner's Note: "{note_str}"

        Your task:
        1. Write a beautiful, heartwarming 2-3 sentence story about this specific memory.
        2. Extract structured metadata.

        Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
        {{
            "story": "The heartwarming story here.",
            "tags": {{
                "objects": ["object1", "object2"],
                "mood": "happy",
                "setting": "beach"
            }}
        }}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b", # Active free-tier text model
            response_format={"type": "json_object"}
        )
        
        result_text = chat_completion.choices[0].message.content
        return json.loads(result_text)
        
    except Exception as e:
        print(f"Groq Story Generation Error: {e}")
        raise e