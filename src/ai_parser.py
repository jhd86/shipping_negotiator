import google.genai as genai
from google.genai import types
import json
import re
from typing import Union
from src.config import GEMINI_API_KEY


def parse_quote_with_ai(email_body: str) -> Union[float, None]:
    """
    Uses the Gemini API via the genai.Client to parse the quote from an email body,
    aligning with the official documentation.
    """
    try:
        # Use the client as shown in the documentation.
        # It automatically finds the API key from environment variables if not passed directly.
        client = genai.Client(api_key=GEMINI_API_KEY)

        # A more direct prompt to ensure only JSON is returned.
        prompt = f"""
        Analyze the following email content and extract the total price quote.
        Your response MUST be only a valid JSON object. Do not include any other text,
        greetings, or explanations.

        If a price is found, the JSON object must look like this: {{"price": 1234.56}}
        If no price quote is mentioned, return this exact JSON: {{"price": null}}

        Email content to analyze:
        ---
        {email_body}
        ---
        """

        # Use the exact method from the documentation: client.models.generate_content
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        clean_text = re.sub(r'```json\n(.*?)\n```', r'\1', response.text, flags=re.DOTALL)

        # The response.text should now be a clean JSON string
        json_response = json.loads(clean_text)

        price = json_response.get("price")
        return float(price) if price is not None else None

    except json.JSONDecodeError as e:
        print(f"GEMINI PARSER ERROR: Failed to decode JSON. Raw response was: {response.text}. Error: {e}")
        return None
    except Exception as e:
        print(f"GEMINI PARSER ERROR: An unexpected error occurred: {e}")
        return None
