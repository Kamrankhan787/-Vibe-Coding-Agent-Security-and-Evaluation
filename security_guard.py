import re
from typing import Dict

class SecurityGuard:
    """
    Security module to protect the AI agent from malicious inputs
    and detect policy violations.
    """
    def __init__(self):
        # Heuristic-based prompt injection detection patterns
        self.injection_patterns = [
            r"ignore previous instructions",
            r"override policy",
            r"execute command",
            r"delete files",
            r"system prompt"
        ]
        
        # Policy violation and suspicious content patterns
        self.suspicious_patterns = [
            r"cryptocurrency purchase",
            r"gift cards?",
            r"personal vacation",
            r"gaming equipment"
        ]

    def analyze_input(self, text: str) -> Dict[str, str]:
        """
        Analyzes the input text for both prompt injection and suspicious content.
        Returns a dictionary with status and reason.
        """
        text_lower = text.lower()
        
        # Check for prompt injection
        for pattern in self.injection_patterns:
            if re.search(pattern, text_lower):
                return {
                    "status": "blocked",
                    "reason": "Prompt Injection Detected"
                }

        # Check for suspicious content
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower):
                return {
                    "status": "blocked",
                    "reason": "Suspicious Expense Detected"
                }
                
        # If safe
        return {
            "status": "approved",
            "reason": "Safe"
        }
