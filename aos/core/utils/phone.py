import re

def normalize_phone(phone: str, default_country_code: str = "254") -> str:
    """
    Normalize phone number to E.164 format.
    
    Standardizes numbers for cross-border compatibility:
    - 07... -> +2547... (local to E.164)
    - 2547... -> +2547... (missing plus)
    - +2547... -> +2547... (already correct)
    
    Args:
        phone: Raw phone number string
        default_country_code: Country code to apply if number is local (default: Kenya)
        
    Returns:
        Normalized E.164 string
    """
    if not phone:
        return ""
        
    # Remove all non-numeric characters except leading +
    # If + is in the middle, it's invalid anyway, but we'll be surgical.
    clean = re.sub(r'(?<!^)\+|[^\d+]', '', phone)
    
    if clean.startswith('+'):
        return clean
    
    if clean.startswith('0'):
        # Local format (e.g., 0712345678)
        return f"+{default_country_code}{clean[1:]}"
    
    # Assume it starts with a country code but lacks + (e.g., 254712345678)
    return f"+{clean}"
