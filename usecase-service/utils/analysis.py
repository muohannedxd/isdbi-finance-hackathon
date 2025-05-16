"""
Analysis utilities for the Islamic Finance API.
"""

import os
import json
import logging
from datetime import datetime
from langchain_together import ChatTogether
from langchain_google_genai import ChatGoogleGenerativeAI
from .constants import STANDARDS_INFO, API_METHOD, TOGETHER_MODEL, GEMINI_MODEL
from .language import detect_language

logger = logging.getLogger("islamic_finance_api")

def detect_anomalies(result, transaction_text):
    """
    Detect anomalies in the analysis.
    
    Args:
        result (dict): The analysis result
        transaction_text (str): The original transaction text
        
    Returns:
        list: List of detected anomalies
    """
    anomalies = []
    if 'anomalies' in result and result['anomalies']:
        anomalies.extend(result['anomalies'])
    if result.get('applicable_standards'):
        weights = [std['weight'] for std in result['applicable_standards']]
        if weights and max(weights) < 60:
            anomalies.append(f"Low confidence: Highest standard match is only {max(weights)}%")
        standards = [std['standard'] for std in result['applicable_standards'] if std['weight'] > 50]
        incompatible_pairs = [
            ('FAS 4', 'FAS 28'),
            ('FAS 7', 'FAS 32'),
            ('FAS 10', 'FAS 7')
        ]
        for pair in incompatible_pairs:
            if pair[0] in standards and pair[1] in standards:
                anomalies.append(f"Unusual combination: {pair[0]} and {pair[1]} rarely appear in the same transaction")
    if not result.get('primary_standard') or result.get('primary_standard') == "Unknown":
        anomalies.append("Could not determine a primary standard with confidence")
    return anomalies

def analyze_transaction(transaction_text, model=None, temperature=0.2):
    """
    Analyze a transaction using the configured LLM API (Gemini or Together AI) via LangChain.
    
    Args:
        transaction_text (str): The transaction text to analyze
        model (str, optional): The model to use for analysis. If None, uses the default model based on API_METHOD.
        temperature (float): Temperature setting for the model
        
    Returns:
        dict: Analysis result
    """
    start_time = datetime.now()
    lang = detect_language(transaction_text)
    try:
        prompt = f"""
        You are an expert in Islamic Finance, AAOIFI Financial Accounting Standards (FAS), and Shari'a Standards (SS).
        Please analyze this financial transaction and identify which AAOIFI standards apply (both FAS and SS). 
        Focus specifically on the five selected standards (FAS 4, 7, 10, 28, and 32).
        If more than one standard might apply, provide weighted probabilities and reasoning.
        The transaction you're analyzing is in {lang} language.
        Transaction details:
        {transaction_text}
        Standards information:
        {STANDARDS_INFO}
        First, think through this step by step:
        1. What type of Islamic financial contract is being described?
        2. What are the key features of this transaction that might apply to specific standards?
        3. Are there any unusual or anomalous elements in this transaction?
        4. Which standards might be applicable, and what are the key criteria from each?
        5. How strongly does each standard apply to this transaction?
        Provide your response in JSON format with:
        1. A list of applicable standards with probability weights (0-100), including both FAS and SS
        2. Brief reasoning for each standard
        3. The most applicable standard with detailed justification
        4. The most applicable Shari'a Standard (SS) if any are relevant
        5. Your step-by-step thinking process
        6. Any anomalies or unusual aspects detected in the transaction
        Format:
        {{
            "applicable_standards": [
                {{"standard": "FAS X", "weight": 90, "reason": "brief reason"}},
                {{"standard": "SS Y", "weight": 60, "reason": "brief reason"}}
            ],
            "primary_standard": "FAS X",
            "primary_sharia_standard": "SS Y",
            "detailed_justification": "detailed explanation",
            "thinking_process": ["step 1 thinking", "step 2 thinking", "step 3 thinking"],
            "anomalies": ["any unusual aspects", "potential compliance issues", "inconsistencies"]
        }}
        """
        # Use the appropriate LLM based on API_METHOD
        if model is None:
            # Use default model based on API_METHOD
            model = TOGETHER_MODEL if API_METHOD == "together" else GEMINI_MODEL
            
        if API_METHOD == "together":
            llm = ChatTogether(
                model=model,
                temperature=temperature,
                together_api_key=os.getenv("TOGETHER_API_KEY")
            )
        else:  # Use Gemini
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Response was not valid JSON. Attempting to extract JSON...")
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                try:
                    result = json.loads(response_text[start:end])
                except json.JSONDecodeError:
                    logger.error("Failed to extract valid JSON from response.")
                    result = {
                        "applicable_standards": [],
                        "primary_standard": "Unknown",
                        "primary_sharia_standard": "None",
                        "detailed_justification": "Error parsing response",
                        "thinking_process": [],
                        "anomalies": ["Error in processing response"]
                    }
            else:
                logger.error("Could not find JSON content in response.")
                result = {
                    "applicable_standards": [],
                    "primary_standard": "Unknown",
                    "primary_sharia_standard": "None",
                    "detailed_justification": "Error parsing response",
                    "thinking_process": [],
                    "anomalies": ["Error in processing response"]
                }
        all_anomalies = detect_anomalies(result, transaction_text)
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        response_data = {
            **result,
            "transaction_text": transaction_text,
            "transaction_language": lang,
            "processing_time": processing_time
        }
        return response_data
    except Exception as e:
        logger.error(f"Error analyzing transaction: {str(e)}")
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        return {
            "applicable_standards": [],
            "primary_standard": "Error",
            "primary_sharia_standard": "None",
            "detailed_justification": f"Error analyzing transaction: {str(e)}",
            "thinking_process": [],
            "anomalies": [f"API Error: {str(e)}"],
            "transaction_text": transaction_text,
            "transaction_language": lang,
            "processing_time": processing_time
        }
