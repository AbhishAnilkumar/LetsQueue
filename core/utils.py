import hashlib

def generate_anon_token(ip_address: str, user_agent: str, salt: str = "LetsQueue_2025") -> str:
    """
    Generate anonymous token from IP + User Agent + Salt
    This prevents duplicate joins from same user
    """
    combined = f"{ip_address}:{user_agent}:{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()


def get_client_ip(request) -> str:
    """Extract real client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request) -> str:
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')
