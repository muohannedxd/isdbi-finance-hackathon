"""
Script to clear the response cache for the Islamic Finance API.
"""

import os
import pickle

def clear_cache(cache_file="response_cache.pkl"):
    """
    Clear the response cache.
    
    Args:
        cache_file (str): Path to the cache file
        
    Returns:
        bool: True if cache was cleared, False otherwise
    """
    try:
        if os.path.exists(cache_file):
            # Option 1: Delete the cache file
            os.remove(cache_file)
            print(f"Cache file '{cache_file}' has been deleted.")
            return True
        else:
            print(f"Cache file '{cache_file}' does not exist. Nothing to clear.")
            return False
    except Exception as e:
        print(f"Error clearing cache: {str(e)}")
        return False

def reset_cache(cache_file="response_cache.pkl"):
    """
    Reset the cache to an empty dictionary instead of deleting the file.
    
    Args:
        cache_file (str): Path to the cache file
        
    Returns:
        bool: True if cache was reset, False otherwise
    """
    try:
        # Create an empty cache dictionary
        empty_cache = {}
        with open(cache_file, "wb") as f:
            pickle.dump(empty_cache, f)
        print(f"Cache file '{cache_file}' has been reset to empty.")
        return True
    except Exception as e:
        print(f"Error resetting cache: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear or reset the response cache.")
    parser.add_argument("--reset", action="store_true", help="Reset cache to empty instead of deleting")
    parser.add_argument("--file", type=str, default="response_cache.pkl", help="Path to cache file")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_cache(args.file)
    else:
        clear_cache(args.file)
