"""
Input validation and sanitization module.
Provides security hardening for all user inputs.
"""

import re
import html
from typing import Optional

# Maximum allowed lengths
MAX_CLAIM_LENGTH = 2000
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def sanitize_claim_text(text: str, max_length: int = MAX_CLAIM_LENGTH) -> str:
    """
    Sanitize user-provided claim text to prevent prompt injection.
    
    This is CRITICAL for security as user input is passed to LLMs.
    
    Args:
        text: Raw user input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text safe for LLM prompts
    """
    if not text:
        return ""
    
    # 1. Truncate to max length
    text = text[:max_length]
    
    # 2. Remove control characters (except newlines which we'll handle)
    text = ''.join(c for c in text if c.isprintable() or c in '\n\t ')
    
    # 3. Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # 4. Remove potential injection patterns
    # Block common prompt injection prefixes
    injection_patterns = [
        r'ignore\s+(previous|all|above)\s+instructions?',
        r'forget\s+(everything|all)',
        r'new\s+instructions?:',
        r'system\s*:',
        r'assistant\s*:',
        r'user\s*:',
    ]
    for pattern in injection_patterns:
        text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE)
    
    # 5. Escape quotes that could break JSON parsing
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    
    return text.strip()


def validate_claim_input(text: Optional[str]) -> str:
    """
    Validate and sanitize claim text input.
    Raises ValidationError if invalid.
    
    Args:
        text: User input to validate
        
    Returns:
        Validated and sanitized text
        
    Raises:
        ValidationError: If input is invalid
    """
    if not text:
        raise ValidationError("Claim text is required")
    
    text = text.strip()
    
    if len(text) < 3:
        raise ValidationError("Claim is too short (minimum 3 characters)")
    
    if len(text) > MAX_CLAIM_LENGTH:
        raise ValidationError(f"Claim exceeds maximum length of {MAX_CLAIM_LENGTH} characters")
    
    # Check for pure gibberish (no alphabetic characters)
    if not any(c.isalpha() for c in text):
        raise ValidationError("Claim must contain text characters")
    
    return sanitize_claim_text(text)


def validate_image_upload(file_data: bytes, filename: str) -> bool:
    """
    Validate uploaded image file.
    
    Args:
        file_data: Raw file bytes
        filename: Original filename
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    # Check file size
    if len(file_data) > MAX_IMAGE_SIZE:
        raise ValidationError(f"Image exceeds maximum size of {MAX_IMAGE_SIZE // (1024*1024)}MB")
    
    # Check file extension
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    ext = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
    if ext not in allowed_extensions:
        raise ValidationError(f"Invalid image type. Allowed: {', '.join(allowed_extensions)}")
    
    # Check magic bytes (file signature)
    signatures = {
        b'\x89PNG': 'png',
        b'\xff\xd8\xff': 'jpeg',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'RIFF': 'webp',
    }
    
    valid_signature = False
    for sig in signatures:
        if file_data[:len(sig)] == sig:
            valid_signature = True
            break
    
    if not valid_signature:
        raise ValidationError("File does not appear to be a valid image")
    
    return True


def escape_html_content(text: str) -> str:
    """
    Escape HTML content to prevent XSS attacks.
    Use this for any user-provided content displayed in web interfaces.
    
    Args:
        text: Text that may contain HTML
        
    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    return html.escape(str(text))


def sanitize_url(url: str) -> str:
    """
    Sanitize URL for display.
    
    Args:
        url: URL string
        
    Returns:
        Sanitized URL safe for display
    """
    if not url:
        return ""
    
    # Only allow http/https
    if not url.startswith(('http://', 'https://')):
        return ""
    
    # Remove potential XSS vectors
    dangerous_patterns = ['javascript:', 'data:', 'vbscript:']
    url_lower = url.lower()
    for pattern in dangerous_patterns:
        if pattern in url_lower:
            return ""
    
    return html.escape(url)
