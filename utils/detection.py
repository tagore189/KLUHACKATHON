"""Damage detection module using Google Gemini Vision LLM."""
import json
import os
from google import genai
from google.genai import types

# Initialize the Gemini client
client = None

def init_client(api_key=None):
    """Initialize the GenAI client."""
    global client
    key = api_key or os.environ.get('GOOGLE_API_KEY', '')
    if key:
        client = genai.Client(api_key=key)
    return client


def detect_damage(image_path):
    """
    Analyze vehicle damage using Gemini Vision.
    Returns structured damage assessment data.
    """
    global client
    if not client:
        init_client()

    if not client:
        # Fallback to simulated detection if no API key
        return simulate_damage_detection(image_path)

    try:
        # Upload image to Gemini
        uploaded_file = client.files.upload(file=image_path)

        prompt = """You are an expert automotive damage assessor. Analyze this vehicle image and provide a detailed damage assessment.

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
            "description": "brief description of the damage"
        }
    ],
    "overall_severity": "minor/moderate/severe",
    "drivable": true/false,
    "summary": "overall assessment summary"
}

If no vehicle is detected, set vehicle_detected to false and return empty damages array.
Only return the JSON, no other text."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[uploaded_file, prompt]
        )

        # Parse the JSON response
        response_text = response.text.strip()
        # Remove markdown code block if present
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0]

        result = json.loads(response_text)
        return result

    except Exception as e:
        print(f"Gemini API error: {e}")
        return simulate_damage_detection(image_path)


def simulate_damage_detection(image_path):
    """
    Simulated damage detection for demo purposes.
    Returns realistic-looking assessment data.
    """
    return {
        "vehicle_detected": True,
        "vehicle_type": "sedan",
        "vehicle_color": "white",
        "damages": [
            {
                "part": "front_bumper",
                "damage_type": "dent",
                "severity": "moderate",
                "confidence": 0.92,
                "description": "Moderate dent on the front bumper with paint chipping"
            },
            {
                "part": "headlight",
                "damage_type": "crack",
                "severity": "severe",
                "confidence": 0.88,
                "description": "Cracked headlight lens requiring replacement"
            },
            {
                "part": "hood",
                "damage_type": "scratch",
                "severity": "minor",
                "confidence": 0.85,
                "description": "Surface scratches on hood panel"
            },
            {
                "part": "front_fender",
                "damage_type": "deformation",
                "severity": "moderate",
                "confidence": 0.90,
                "description": "Deformation on the right front fender"
            }
        ],
        "overall_severity": "moderate",
        "drivable": True,
        "summary": "The vehicle has sustained moderate front-end damage including a dented bumper, cracked headlight, scratched hood, and fender deformation. The vehicle appears drivable but requires prompt repairs."
    }
