"""
Utility module for managing validated examples.
This module stores and retrieves validated examples for different AAOIFI standards.
Each standard can have a maximum of 2 examples.
"""

import os
import json
import logging

logger = logging.getLogger("islamic_finance_api")

# File to store validated examples
EXAMPLES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "validated_examples.json")

# Standard types (mapping from standard name to FAS number)
STANDARD_MAPPINGS = {
    "MURABAHA": "FAS 4",
    "SALAM": "FAS 7",
    "ISTISNA": "FAS 10",
    "IJARAH": "FAS 28", 
    "SUKUK": "FAS 32"
}

def get_examples_for_standard(standard_type):
    """
    Retrieve validated examples for a specific standard type.
    
    Args:
        standard_type (str): The standard type (e.g., "MURABAHA", "IJARAH")
        
    Returns:
        list: List of examples for the standard, or empty list if none
    """
    examples = load_examples()
    return examples.get(standard_type, [])

def add_example(standard_type, query, response):
    """
    Add a new validated example for a specific standard type.
    Maintains a maximum of 2 examples per standard type.
    When adding a third example, it will override the second example,
    preserving the first example as a reference.
    
    Args:
        standard_type (str): The standard type (e.g., "MURABAHA", "IJARAH")
        query (str): User's question or scenario
        response (str): The validated response
        
    Returns:
        bool: True if example was added successfully, False otherwise
    """
    if not standard_type or not query or not response:
        return False
    
    # Load existing examples
    examples = load_examples()
    
    # Initialize standard type if not exists
    if standard_type not in examples:
        examples[standard_type] = []
    
    # Check if we already have 2 examples
    if len(examples[standard_type]) >= 2:
        # Override the second (index 1) example, keeping the first example as reference
        examples[standard_type][1] = {
            "query": query,
            "response": response
        }
        logger.info(f"Overrode second example for {standard_type}")
    else:
        # Add new example
        examples[standard_type].append({
            "query": query,
            "response": response
        })
        logger.info(f"Added new validated example for {standard_type}")
    
    # Save examples back to file
    save_examples(examples)
    logger.info(f"Updated examples for {standard_type} ({STANDARD_MAPPINGS.get(standard_type, 'Unknown')})")
    return True

def load_examples():
    """
    Load all validated examples from file.
    
    Returns:
        dict: Dictionary of all examples by standard type
    """
    try:
        if os.path.exists(EXAMPLES_FILE):
            with open(EXAMPLES_FILE, 'r') as file:
                return json.load(file)
    except Exception as e:
        logger.error(f"Error loading validated examples: {str(e)}")
    return {}

def save_examples(examples):
    """
    Save all validated examples to file.
    
    Args:
        examples (dict): Dictionary of examples by standard type
    """
    try:
        with open(EXAMPLES_FILE, 'w') as file:
            json.dump(examples, file, indent=2)
    except Exception as e:
        logger.error(f"Error saving validated examples: {str(e)}")

def get_examples_as_few_shot(standard_type):
    """
    Format examples for the given standard as few-shot examples.
    
    Args:
        standard_type (str): The standard type (e.g., "MURABAHA", "IJARAH")
        
    Returns:
        str: Formatted few-shot examples or empty string if none
    """
    examples = get_examples_for_standard(standard_type)
    if not examples:
        return ""
    
    formatted_examples = ""
    for i, example in enumerate(examples):
        formatted_examples += f"\nExample {i+1}:\nScenario: {example['query']}\nResponse: {example['response']}\n"
    
    return formatted_examples