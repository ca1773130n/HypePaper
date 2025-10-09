from typing import Optional
from sotapapers.core.settings import Settings

def apply_url_prefix(url: str, settings: Settings) -> str:
    """
    Apply URL prefix from settings to the given URL.
    
    Args:
        url: The original URL
        settings: Settings object containing the url_prefix configuration
        
    Returns:
        The URL with prefix applied if configured, otherwise the original URL
    """
    if not url:
        return url
    
    # Get URL prefix from settings
    url_prefix = settings.config.paper_crawler.url_prefix
    
    # If no prefix is configured, return the original URL
    if not url_prefix or len(url_prefix) == 0:
        return url
    
    # Don't apply prefix to relative URLs or URLs that already start with the prefix
    if not url.startswith(('http://', 'https://')) or url.startswith(url_prefix):
        return url
    
    # Apply the prefix
    return url_prefix + '/' + url

def get_url_with_prefix(base_url: str, path: str, settings: Settings) -> str:
    """
    Construct a URL from base URL and path, then apply prefix from settings.
    
    Args:
        base_url: The base URL
        path: The path to append to the base URL
        settings: Settings object containing the url_prefix configuration
        
    Returns:
        The constructed URL with prefix applied if configured
    """
    if not base_url:
        return path
    
    # Ensure base_url doesn't end with / and path doesn't start with /
    base_url = base_url.rstrip('/')
    path = path.lstrip('/') if path else ''
    
    # Construct the full URL
    full_url = f"{base_url}/{path}" if path else base_url
    
    # Apply prefix
    return apply_url_prefix(full_url, settings) 