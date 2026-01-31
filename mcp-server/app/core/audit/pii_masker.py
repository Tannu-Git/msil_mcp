"""PII masking utilities for logging compliance."""

import re
from typing import Any, Dict, List, Union


class PIIMasker:
    """Mask PII in logs and audit trails."""
    
    # Regex patterns for PII detection
    PHONE_PATTERN = re.compile(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    @staticmethod
    def mask_phone(text: str) -> str:
        """Mask phone numbers in text.
        
        Example: 9876543210 -> 98******10
        """
        if not text:
            return text
        
        def mask_match(match):
            phone = match.group()
            if len(phone) >= 4:
                return f"{phone[:2]}{'*' * (len(phone) - 4)}{phone[-2:]}"
            return "***"
        
        return PIIMasker.PHONE_PATTERN.sub(mask_match, text)
    
    @staticmethod
    def mask_email(text: str) -> str:
        """Mask email addresses in text.
        
        Example: user@example.com -> us***@example.com
        """
        if not text:
            return text
        
        def mask_match(match):
            email = match.group()
            parts = email.split('@')
            if len(parts) == 2 and len(parts[0]) >= 2:
                return f"{parts[0][:2]}***@{parts[1]}"
            return "***"
        
        return PIIMasker.EMAIL_PATTERN.sub(mask_match, text)
    
    @staticmethod
    def mask_text(text: str) -> str:
        """Mask all PII in text."""
        if not text:
            return text
        
        text = PIIMasker.mask_phone(text)
        text = PIIMasker.mask_email(text)
        return text
    
    @staticmethod
    def mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask PII in dictionary."""
        if not data:
            return data
        
        masked = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Mask string values
                masked[key] = PIIMasker.mask_text(value)
            elif isinstance(value, dict):
                # Recursively mask nested dicts
                masked[key] = PIIMasker.mask_dict(value)
            elif isinstance(value, list):
                # Mask items in lists
                masked[key] = PIIMasker.mask_list(value)
            else:
                # Keep other types as-is
                masked[key] = value
        
        return masked
    
    @staticmethod
    def mask_list(data: List[Any]) -> List[Any]:
        """Mask PII in list items."""
        if not data:
            return data
        
        masked = []
        for item in data:
            if isinstance(item, str):
                masked.append(PIIMasker.mask_text(item))
            elif isinstance(item, dict):
                masked.append(PIIMasker.mask_dict(item))
            elif isinstance(item, list):
                masked.append(PIIMasker.mask_list(item))
            else:
                masked.append(item)
        
        return masked


# Global instance
pii_masker = PIIMasker()
