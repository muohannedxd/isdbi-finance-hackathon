"""
Caching utilities for the Islamic Finance API with semantic search capabilities.
"""

import pickle
import hashlib
import os
import random
import numpy as np
from datetime import datetime, timedelta
from langchain_huggingface import HuggingFaceEmbeddings

# Cache file for storing responses
DEFAULT_CACHE_FILE = "response_cache.pkl"

# Cache file for storing embeddings
EMBEDDINGS_CACHE_FILE = "embeddings_cache.pkl"

# Default embedding model
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

# Cache entry expiration (in days)
CACHE_EXPIRY_DAYS = 30

# Similarity threshold for considering queries as semantically equivalent
SIMILARITY_THRESHOLD = 0.92

# Global embeddings model (lazy loaded)
_embeddings_model = None

def get_embeddings_model():
    """
    Get or initialize the embeddings model.
    
    Returns:
        HuggingFaceEmbeddings: The embeddings model
    """
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=DEFAULT_EMBEDDING_MODEL,
            cache_folder="./models/"
        )
    return _embeddings_model

def compute_embedding(text):
    """
    Compute embeddings for a text.
    
    Args:
        text (str): The text to compute embeddings for
        
    Returns:
        list: The embedding vector
    """
    model = get_embeddings_model()
    return model.embed_query(text)

def cosine_similarity(vec1, vec2):
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1 (list): First vector
        vec2 (list): Second vector
        
    Returns:
        float: Cosine similarity score between 0 and 1
    """
    if not isinstance(vec1, np.ndarray):
        vec1 = np.array(vec1)
    if not isinstance(vec2, np.ndarray):
        vec2 = np.array(vec2)
    
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def get_cached_response(prompt, cache_file=DEFAULT_CACHE_FILE, force_reload=False):
    """
    Get cached response using semantic similarity instead of exact matching.
    
    Args:
        prompt (str): The prompt to get cached response for
        cache_file (str): Path to the cache file
        force_reload (bool): Whether to force a reload regardless of cache
        
    Returns:
        str or None: The cached response if a similar prompt exists, None otherwise
    """
    if force_reload:
        return None
        
    try:
        # Generate embedding for the current prompt
        query_embedding = compute_embedding(prompt)
        
        # Load both caches
        with open(cache_file, "rb") as f:
            response_cache = pickle.load(f)
            
        try:
            with open(EMBEDDINGS_CACHE_FILE, "rb") as f:
                embeddings_cache = pickle.load(f)
        except (FileNotFoundError, EOFError):
            # If embeddings cache doesn't exist, create it from response cache
            embeddings_cache = {}
            for prompt_hash in response_cache:
                # Skip if the entry is missing a timestamp or has expired
                if not isinstance(response_cache[prompt_hash], dict) or "timestamp" not in response_cache[prompt_hash]:
                    continue
                if "prompt" in response_cache[prompt_hash]:
                    cached_prompt = response_cache[prompt_hash]["prompt"]
                    embeddings_cache[prompt_hash] = compute_embedding(cached_prompt)
                    
        # Find the most similar prompt in the cache
        best_similarity = -1
        best_hash = None
        
        for prompt_hash, embedding in embeddings_cache.items():
            if prompt_hash not in response_cache:
                continue
                
            # Skip if the entry is missing a timestamp or has expired
            if not isinstance(response_cache[prompt_hash], dict) or "timestamp" not in response_cache[prompt_hash]:
                continue
                
            # Check if the cache entry has expired
            entry_timestamp = response_cache[prompt_hash]["timestamp"]
            if datetime.now() - entry_timestamp > timedelta(days=CACHE_EXPIRY_DAYS):
                continue
                
            similarity = cosine_similarity(query_embedding, embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_hash = prompt_hash
        
        # If we found a similar prompt above the threshold
        if best_similarity > SIMILARITY_THRESHOLD and best_hash is not None:
            print(f"Found semantically similar cached response (similarity: {best_similarity:.4f})")
            
            # Retrieve the cached response
            cached_entry = response_cache[best_hash]
            cached_response = cached_entry["response"]
            
            # Apply slight variations to the response to avoid exact repetition
            if random.random() < 0.7:  # 70% chance to add variations
                cached_response = add_response_variations(cached_response)
                
            return cached_response
            
    except (FileNotFoundError, EOFError) as e:
        print(f"Cache file error: {e}")
    except Exception as e:
        print(f"Error retrieving from cache: {e}")
        
    return None

def add_response_variations(response):
    """
    Add slight variations to a response to avoid exact repetition.
    
    Args:
        response (str): The original response
        
    Returns:
        str: The response with slight variations
    """
    # Dictionary of variation patterns and their replacements
    variations = {
        "Please note": ["Note that", "It's important to note", "Keep in mind"],
        "In accordance with": ["Following", "As per", "In line with"],
        "According to": ["Based on", "As stated in", "Referring to"],
        "is recognized": ["is accounted for", "is recorded", "is treated"],
        "Additionally,": ["Furthermore,", "Moreover,", "In addition,"],
        "should be": ["needs to be", "must be", "has to be"],
        "In summary,": ["To summarize,", "In conclusion,", "To conclude,"]
    }
    
    modified_response = response
    
    # Apply a small number of random variations
    for phrase, alternatives in variations.items():
        if phrase in modified_response and random.random() < 0.5:  # 50% chance to apply each variation
            modified_response = modified_response.replace(phrase, random.choice(alternatives), 1)
    
    return modified_response

def cache_response(prompt, response, cache_file=DEFAULT_CACHE_FILE):
    """
    Cache the response using both hash and embeddings for future semantic lookup.
    
    Args:
        prompt (str): The prompt to cache response for
        response (str): The response to cache
        cache_file (str): Path to the cache file
    """
    try:
        # Generate a hash for the prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        # Compute embedding for the prompt
        prompt_embedding = compute_embedding(prompt)
        
        # Load existing response cache or create a new one
        try:
            with open(cache_file, "rb") as f:
                response_cache = pickle.load(f)
        except (FileNotFoundError, EOFError):
            response_cache = {}
        
        # Load existing embeddings cache or create a new one
        try:
            with open(EMBEDDINGS_CACHE_FILE, "rb") as f:
                embeddings_cache = pickle.load(f)
        except (FileNotFoundError, EOFError):
            embeddings_cache = {}
        
        # Store the response with metadata
        response_cache[prompt_hash] = {
            "response": response,
            "prompt": prompt,
            "timestamp": datetime.now(),
            "standard_type": detect_standard_type_if_available(prompt)
        }
        
        # Store the embedding
        embeddings_cache[prompt_hash] = prompt_embedding
        
        # Save both caches
        with open(cache_file, "wb") as f:
            pickle.dump(response_cache, f)
            
        with open(EMBEDDINGS_CACHE_FILE, "wb") as f:
            pickle.dump(embeddings_cache, f)
            
        print(f"Cached response with hash {prompt_hash[:8]}...")
        
    except Exception as e:
        print(f"Error caching response: {e}")

def detect_standard_type_if_available(prompt):
    """
    Try to detect the standard type from the prompt.
    
    Args:
        prompt (str): The prompt to analyze
        
    Returns:
        str or None: The detected standard type or None
    """
    try:
        # Only import here to avoid circular imports
        from utils.extraction import detect_standard_type
        return detect_standard_type(prompt)
    except:
        return None

def clear_cache(cache_file=DEFAULT_CACHE_FILE):
    """
    Clear all cache files.
    
    Args:
        cache_file (str): Path to the main cache file
        
    Returns:
        bool: True if cache was cleared, False otherwise
    """
    try:
        success = False
        
        if os.path.exists(cache_file):
            os.remove(cache_file)
            success = True
            
        if os.path.exists(EMBEDDINGS_CACHE_FILE):
            os.remove(EMBEDDINGS_CACHE_FILE)
            success = True
            
        return success
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False

def clear_expired_entries(cache_file=DEFAULT_CACHE_FILE):
    """
    Clear expired entries from the cache.
    
    Args:
        cache_file (str): Path to the cache file
        
    Returns:
        int: Number of entries cleared
    """
    try:
        # Load existing caches
        try:
            with open(cache_file, "rb") as f:
                response_cache = pickle.load(f)
        except (FileNotFoundError, EOFError):
            return 0
            
        try:
            with open(EMBEDDINGS_CACHE_FILE, "rb") as f:
                embeddings_cache = pickle.load(f)
        except (FileNotFoundError, EOFError):
            embeddings_cache = {}
        
        # Track how many entries we clear
        cleared_count = 0
        
        # Current time for comparison
        now = datetime.now()
        
        # List of keys to remove (to avoid modifying dict during iteration)
        keys_to_remove = []
        
        # Find expired entries
        for prompt_hash, entry in response_cache.items():
            if not isinstance(entry, dict) or "timestamp" not in entry:
                keys_to_remove.append(prompt_hash)
                cleared_count += 1
                continue
                
            entry_timestamp = entry["timestamp"]
            if now - entry_timestamp > timedelta(days=CACHE_EXPIRY_DAYS):
                keys_to_remove.append(prompt_hash)
                cleared_count += 1
        
        # Remove expired entries
        for key in keys_to_remove:
            if key in response_cache:
                del response_cache[key]
            if key in embeddings_cache:
                del embeddings_cache[key]
        
        # Save updated caches if we removed any entries
        if cleared_count > 0:
            with open(cache_file, "wb") as f:
                pickle.dump(response_cache, f)
                
            with open(EMBEDDINGS_CACHE_FILE, "wb") as f:
                pickle.dump(embeddings_cache, f)
        
        return cleared_count
        
    except Exception as e:
        print(f"Error clearing expired entries: {e}")
        return 0
