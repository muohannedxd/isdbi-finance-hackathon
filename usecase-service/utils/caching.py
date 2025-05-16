"""
Caching utilities for the Islamic Finance API.
"""

import pickle
import hashlib

def get_cached_response(prompt, cache_file="response_cache.pkl"):
    """
    Get cached response if it exists.
    
    Args:
        prompt (str): The prompt to get cached response for
        cache_file (str): Path to the cache file
        
    Returns:
        str or None: The cached response if it exists, None otherwise
    """
    try:
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
        if prompt_hash in cache:
            print("Using cached response")
            return cache[prompt_hash]
    except (FileNotFoundError, EOFError):
        pass
    return None

def cache_response(prompt, response, cache_file="response_cache.pkl"):
    """
    Cache the response for future use.
    
    Args:
        prompt (str): The prompt to cache response for
        response (str): The response to cache
        cache_file (str): Path to the cache file
    """
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    try:
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
    except (FileNotFoundError, EOFError):
        cache = {}
    cache[prompt_hash] = response
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)
