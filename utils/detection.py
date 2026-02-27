"""Damage detection module using OpenAI GPT-4o Vision."""
import json
import os
import base64
from openai import OpenAI

# Initialize the OpenAI client
client = None

def init_client(api_key=None):
    """Initialize the OpenAI client."""
    global client
    key = api_key or os.environ.get('OPENAI_API_KEY', '')
    if key:
        client = OpenAI(api_key=key)
    return client


def encode_image(image_path):
    """Encode the image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def detect_damage(image_path):
    """
    Analyze vehicle damage using OpenAI GPT-4o.
    Returns structured damage assessment data.
    """
    global client
    if not client:
        init_client()

    if not client:
        raise ConnectionError("OpenAI client not initialized. Please ensure OPENAI_API_KEY is set in your .env file.")

    try:
        # Encode image
        base64_image = encode_image(image_path)
        
        # Determine media type
        ext = image_path.rsplit('.', 1)[-1].lower()
        media_type = f"image/{ext}" if ext != 'jpg' else 'image/jpeg'

        prompt = """You are a highly detailed real-time automotive damage assessor.
Analyze this vehicle image in detail to identify CURRENT damage.

Return your analysis as a JSON object with this exact structure:
{
    "vehicle_detected": true/false,
    "vehicle_type": "sedan/suv/truck/sports/van/other",
    "vehicle_color": "color",
    "damages": [
        {
            "part": "part_name (use snake_case, e.g. front_bumper, rear_fender, hood, door, headlight, taillight, windshield, side_mirror, grille, wheel_rim, rocker_panel, trunk, roof, front_fender, rear_bumper)",
            "damage_type": "scratch/dent/crack/shatter/deformation/paint_damage/structural",
            "severity": "minor/moderate/severe",
            "confidence": 0.0-1.0,
            "description": "brief evidence-based description of the damage"
        }
    ],
    "overall_severity": "minor/moderate/severe",
    "drivable": true/false,
    "summary": "overall real-time assessment summary based on visual evidence"
}

IMPORTANT: Be extremely specific about damage locations and types.
Only return the JSON, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )

        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        error_msg = str(e)
        print(f"OpenAI API error: {error_msg}")
        raise e
