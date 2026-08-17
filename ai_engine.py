"""
ZERX XIT - AI Engine
====================
Google Gemini API integration for advanced optimization.
"""
import os
import json
import requests
import config

class AIEngine:
    """Interface to Google Gemini API for gaming optimization."""

    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_MODEL
        self.temperature = config.GEMINI_TEMPERATURE
        self.max_tokens = config.GEMINI_MAX_TOKENS
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def optimize(self, device_info, sensitivity, play_style, vip=False):
        """Get AI-optimized tips from Gemini."""
        if self.api_key == 'YOUR_GEMINI_API_KEY_HERE':
            raise ValueError("Gemini API key not configured")

        device_str = f"{device_info.get('brand', 'Unknown')} {device_info.get('model', 'Unknown')}"
        proc = device_info.get('processor', 'Unknown')
        gpu = device_info.get('gpu', 'Unknown')
        ram = device_info.get('ram', '4GB')
        refresh = device_info.get('refresh_rate', '60Hz')

        prompt = f"""You are ZERX XIT AI, a Free Fire gaming optimization expert.

DEVICE: {device_str}
PROCESSOR: {proc}
GPU: {gpu}
RAM: {ram}
REFRESH RATE: {refresh}
PLAY STYLE: {play_style}
VIP: {'Yes' if vip else 'No'}

GENERATED SENSITIVITY:
- General: {sensitivity['general']}
- Red Dot: {sensitivity['red_dot']}
- 2X Scope: {sensitivity['scope2x']}
- 4X Scope: {sensitivity['scope4x']}
- Sniper: {sensitivity['sniper']}
- Free Look: {sensitivity['free_look']}
- DPI: {sensitivity['dpi']}

Provide SHORT, professional gaming optimization advice in JSON format:
{{
  "phone_settings": ["tip1", "tip2", "tip3", "tip4"],
  "developer_options": ["tip1", "tip2", "tip3", "tip4"],
  "gaming_tips": ["tip1", "tip2", "tip3", "tip4"],
  "optimization_tips": ["tip1", "tip2", "tip3", "tip4"],
  "battery_tips": ["tip1", "tip2", "tip3", "tip4"],
  "performance_tips": ["tip1", "tip2", "tip3", "tip4"],
  "sensitivity_advice": ["tip1", "tip2", "tip3", "tip4"]
  {',"advanced": ["tip1", "tip2", "tip3", "tip4"]' if vip else ''}
}}

Rules:
- Each array must have exactly 4 items
- Keep each tip under 100 characters
- Be specific to the device hardware
- Focus on Free Fire mobile optimization
- Return ONLY valid JSON, no markdown"""

        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": self.temperature,
                        "maxOutputTokens": self.max_tokens,
                        "responseMimeType": "application/json"
                    }
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            # Extract text from Gemini response
            text = data['candidates'][0]['content']['parts'][0]['text']

            # Clean up potential markdown
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()

            result = json.loads(text)
            return result

        except requests.exceptions.RequestException as e:
            raise ValueError(f"API request failed: {str(e)}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid API response: {str(e)}")

    def test_connection(self):
        """Test if Gemini API is reachable."""
        if self.api_key == 'YOUR_GEMINI_API_KEY_HERE':
            return False, "API key not set"
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": "Say 'ZERX XIT AI Ready'"}]}],
                    "generationConfig": {"maxOutputTokens": 20}
                },
                timeout=10
            )
            if response.status_code == 200:
                return True, "Connected"
            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
