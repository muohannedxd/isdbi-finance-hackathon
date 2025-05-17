"""
Extraction utilities for the Islamic Finance API.
"""

import re
from .constants import (
    STANDARD_TYPE_MURABAHA, STANDARD_TYPE_SALAM, STANDARD_TYPE_ISTISNA,
    STANDARD_TYPE_IJARAH, STANDARD_TYPE_SUKUK
)

def detect_standard_type(query_text):
    """
    Detect which AAOIFI standard applies to the scenario.
    
    Args:
        query_text (str): The query text to analyze
        
    Returns:
        str: The detected standard type or None if no match
    """
    query_lower = query_text.lower()
    murabaha_keywords = [
        'murabaha', 'murabahah', 'cost plus sale', 'cost-plus financing', 
        'deferred payment sale', 'aaoifi fas 4'
    ]
    if any(keyword in query_lower for keyword in murabaha_keywords):
        return STANDARD_TYPE_MURABAHA
    salam_keywords = [
        'salam', 'salaam', 'advance payment', 'future delivery', 
        'parallel salam', 'aaoifi fas 7'
    ]
    if any(keyword in query_lower for keyword in salam_keywords):
        return STANDARD_TYPE_SALAM
    istisna_keywords = [
        'istisna', "istisna'a", 'istisna`a', 'manufacturing contract', 
        'construction contract', 'parallel istisna', 'aaoifi fas 10'
    ]
    if any(keyword in query_lower for keyword in istisna_keywords):
        return STANDARD_TYPE_ISTISNA
    ijarah_keywords = [
        'ijarah', 'ijara', 'lease', 'leasing', 
        'muntahia bittamleek', 'ijara wa iqtina', 
        'right of use', 'rou', 'aaoifi fas 28'
    ]
    if any(keyword in query_lower for keyword in ijarah_keywords):
        return STANDARD_TYPE_IJARAH
    sukuk_keywords = [
        'sukuk', 'investment certificates', 'islamic bonds', 
        'asset-backed securities', 'aaoifi fas 32'
    ]
    if any(keyword in query_lower for keyword in sukuk_keywords):
        return STANDARD_TYPE_SUKUK
    return None

def extract_ijarah_variables(query_text):
    """
    Extract key financial variables from an Ijarah scenario text using regex.
    
    Args:
        query_text (str): The query text to extract variables from
        
    Returns:
        dict: Extracted variables
    """
    patterns = {
        'purchase_price': r'(?:purchased|purchase price|cost|bought).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'import_tax': r'(?:import tax|tax|duty).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'freight_charges': r'(?:freight|shipping|transportation|delivery).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'yearly_rental': r'(?:yearly rental|annual rent|rent per year|annual rental|per year).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'lease_term': r'(?:lease term|term of|period of|duration).*?([0-9,.]+)[\s](?:year|yr|yrs|years)',
        'residual_value': r'(?:residual value|expected.*?value|value at end).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'purchase_option': r'(?:purchase option|option to purchase|purchase price at end).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)'
    }
    extracted_values = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, query_text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                extracted_values[key] = float(value_str)
            except ValueError:
                pass
    return extracted_values

def extract_murabaha_variables(query_text):
    """
    Extract key financial variables from a Murabaha scenario text using regex.
    
    Args:
        query_text (str): The query text to extract variables from
        
    Returns:
        dict: Extracted variables
    """
    patterns = {
        'cost_price': r'(?:cost price|purchase price|acquired for|bought for).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'selling_price': r'(?:selling price|sold for|sale price|sells at).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'profit_rate': r'(?:profit rate|markup|mark-up|margin).*?([0-9,.]+)[\s]*(?:%|percent)',
        'installments': r'(?:installment|instalment|payment).+?([0-9]+)[\s]*(?:payment|installment|monthly|quarterly|annual)',
        'down_payment': r'(?:down payment|advance|initial payment).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)'
    }
    extracted_values = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, query_text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                extracted_values[key] = float(value_str)
            except ValueError:
                pass
    return extracted_values

def extract_istisna_variables(query_text):
    """
    Extract key financial variables from an Istisna'a contract scenario text using regex.
    
    Args:
        query_text (str): The query text to extract variables from
        
    Returns:
        dict: Extracted variables
    """
    patterns = {
        'contract_value': r'(?:price|contract value|agreed price|contract amount).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'total_cost': r'(?:cost|total cost|estimated cost|contractor.*?cost).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'delivery_period': r'(?:delivery|completion|construction).*?([0-9,.]+)[\s]*(?:month|months|year|years)',
        'installments': r'(?:installment|payment).*?([0-9]+)[\s]*(?:quarterly|monthly|annual|installment)',
        'upfront_payment': r'(?:upfront|advance|initial).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'completion_payment': r'(?:completion|final).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)'
    }
    
    extracted_values = {}
    
    # Try specialized patterns first
    contract_match = re.search(r'[Pp]rice:? \$?([0-9,.]+)', query_text)
    if contract_match:
        extracted_values['contract_value'] = float(contract_match.group(1).replace(',', ''))
    
    cost_match = re.search(r'[Cc]ost:? \$?([0-9,.]+)', query_text)
    if cost_match:
        extracted_values['total_cost'] = float(cost_match.group(1).replace(',', ''))
        
    # Look for specific payment patterns in parallel istisna'a scenarios
    upfront_match = re.search(r'\$?([0-9,.]+)\s*upfront', query_text, re.IGNORECASE)
    if upfront_match:
        extracted_values['upfront_payment'] = float(upfront_match.group(1).replace(',', ''))
        
    completion_match = re.search(r'\$?([0-9,.]+)\s*on completion', query_text, re.IGNORECASE)
    if completion_match:
        extracted_values['completion_payment'] = float(completion_match.group(1).replace(',', ''))
    
    # Then try the general patterns
    for key, pattern in patterns.items():
        if key not in extracted_values:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    extracted_values[key] = float(value_str)
                except ValueError:
                    pass
    
    return extracted_values
