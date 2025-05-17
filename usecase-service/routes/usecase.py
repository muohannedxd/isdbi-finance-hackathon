from flask import Blueprint, request, jsonify
import os
import logging
import random
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_together import ChatTogether
from langchain_google_genai import ChatGoogleGenerativeAI

# Import utility modules
from utils.constants import (
    CHROMA_PATH, DEFAULT_EMBEDDING_MODEL, TOGETHER_MODEL, GEMINI_MODEL, API_METHOD,
    STANDARD_TYPE_MURABAHA, STANDARD_TYPE_SALAM, STANDARD_TYPE_ISTISNA, 
    STANDARD_TYPE_IJARAH, STANDARD_TYPE_SUKUK, STANDARD_TYPE_MUSHARAKA
)
from utils.extraction import detect_standard_type, extract_ijarah_variables, extract_murabaha_variables, extract_istisna_variables
from utils.calculation import calculate_ijarah_values, calculate_murabaha_values, calculate_istisna_values
from utils.formatting import format_ijarah_response, format_murabaha_response, format_istisna_response
from utils.caching import get_cached_response, cache_response
from utils.parsing import extract_thinking_process, parse_financial_data
from utils.constants import get_prompt_for_standard

# Create the blueprint for the usecase route
usecase_bp = Blueprint('usecase_bp', __name__)
logger = logging.getLogger("islamic_finance_api")

def process_query(query_text, embedding_model=DEFAULT_EMBEDDING_MODEL, llm_model=None, use_openai=False, force_reload=False):
    """Process a query and return the response using the configured LLM API (Gemini or Together AI) via LangChain."""
    
    # Set default model based on API_METHOD if none provided
    if llm_model is None:
        llm_model = TOGETHER_MODEL if API_METHOD == "together" else GEMINI_MODEL
    
    print(f'API method: {API_METHOD}')
    print(f'LLM model: {llm_model}')
    embedding_function = HuggingFaceEmbeddings(
        model_name=embedding_model,
        cache_folder="./models/"
    )
    if not os.path.exists(CHROMA_PATH):
        raise FileNotFoundError(f"Database not found at {CHROMA_PATH}. Please run create_database.py first.")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    standard_type = detect_standard_type(query_text)
    
    # Handle Ijarah cases with direct calculation
    if standard_type == STANDARD_TYPE_IJARAH:
        variables = extract_ijarah_variables(query_text)
        if 'purchase_price' in variables and 'yearly_rental' in variables and 'lease_term' in variables:
            calculations = calculate_ijarah_values(variables)
            response_text = format_ijarah_response(variables, calculations)
            return {"response": response_text, "sources": ["Calculated based on AAOIFI FAS 28 standards"]}
    
    # Handle Murabaha cases with direct calculation
    elif standard_type == STANDARD_TYPE_MURABAHA:
        variables = extract_murabaha_variables(query_text)
        if 'cost_price' in variables:
            calculations = calculate_murabaha_values(variables)
            response_text = format_murabaha_response(variables, calculations)
            return {"response": response_text, "sources": ["Calculated based on AAOIFI FAS 4 standards"]}
    
    # Handle Istisna'a cases with direct calculation
    elif standard_type == STANDARD_TYPE_ISTISNA and ("percentage" in query_text.lower() or "completion" in query_text.lower()):
        print("\n\n==== PROCESSING ISTISNA'A SCENARIO ====\n")
        variables = extract_istisna_variables(query_text)
        print(f"Extracted variables: {variables}")
        
        # Add description to variables for better context extraction
        variables['description'] = query_text
        
        if 'contract_value' in variables and ('total_cost' in variables or 'parallel istisna' in query_text.lower()):
            calculations = calculate_istisna_values(variables)
            print(f"Calculated values: {calculations}")
            
            # Print quarterly progress for debugging
            print("\nQuarterly Progress:")
            for idx, quarter in enumerate(calculations.get('quarterly_progress', [])):
                print(f"Quarter {idx+1}: {quarter}")
            
            response_text = format_istisna_response(variables, calculations)
            print(f"\nFormatted response (first 200 chars): {response_text[:200]}...")
            print("\n==== END ISTISNA'A PROCESSING ====\n")
            return {"response": response_text, "sources": ["Calculated based on AAOIFI FAS 10 standards"]}
    
    # For other cases, use the LLM
    search_query = query_text
    if standard_type == STANDARD_TYPE_MURABAHA:
        search_query = f"murabaha financing AAOIFI FAS 4 {query_text}"
    elif standard_type == STANDARD_TYPE_SALAM:
        search_query = f"salam contract AAOIFI FAS 7 {query_text}"
    elif standard_type == STANDARD_TYPE_ISTISNA:
        search_query = f"istisna contract AAOIFI FAS 10 {query_text}"
    elif standard_type == STANDARD_TYPE_IJARAH:
        search_query = f"ijarah lease AAOIFI FAS 28 {query_text}"
    elif standard_type == STANDARD_TYPE_SUKUK:
        search_query = f"sukuk investment AAOIFI FAS 32 {query_text}"
    elif standard_type == STANDARD_TYPE_MUSHARAKA:
        search_query = f"musharaka partnership AAOIFI FAS 4 {query_text}"
        
    results = db.similarity_search_with_relevance_scores(search_query, k=5)
    if len(results) == 0 or results[0][1] < -9:
        raise ValueError("Unable to find matching results.")
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(get_prompt_for_standard(standard_type))
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    # Use the semantic caching system with the force_reload parameter
    cached_response = get_cached_response(prompt, force_reload=force_reload)
    if cached_response and not force_reload:
        response_text = cached_response
        print("Using semantically cached response")
    else:
        # Use default model if none provided
        if llm_model is None:
            llm_model = TOGETHER_MODEL if API_METHOD == "together" else GEMINI_MODEL
            
        # Use the appropriate LLM based on API_METHOD
        if API_METHOD == "together":
            llm = ChatTogether(
                model=llm_model,
                temperature=0.3,
                together_api_key=os.getenv("TOGETHER_API_KEY")
            )
        else:  # Use Gemini
            llm = ChatGoogleGenerativeAI(
                model=llm_model,
                temperature=0.3,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Cache the response with our improved caching system
        cache_response(prompt, response_text)
        print("Generated new response and cached it")
        
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    
    # Periodically clean expired cache entries (with 5% probability)
    if random.random() < 0.05:
        from utils.caching import clear_expired_entries
        cleared = clear_expired_entries()
        if cleared > 0:
            print(f"Cleared {cleared} expired cache entries")
            
    return {"response": response_text, "sources": sources}

@usecase_bp.route('', methods=['POST'])
def query_handler():
    """Handle /usecase POST requests"""
    data = request.json
    query_text = data.get("query_text")
    embedding_model = data.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    llm_model = data.get("llm_model", None)
    use_openai = data.get("use_openai", True)
    force_reload = data.get("force_reload", False)
    
    if not query_text:
        return jsonify({"error": "query_text is required"}), 400
    
    try:
        # Process the query
        result = process_query(query_text, embedding_model, llm_model, use_openai, force_reload)
        
        # Extract thinking process if present
        thinking_process = extract_thinking_process(result["response"])
        
        # Parse the response to extract structured financial data
        parsed_result = parse_financial_data(result["response"], query_text)
        
        # Log the response for comparison between backend and frontend
        standard_type = detect_standard_type(query_text)
        
        # Log appropriate messages based on the standard type
        if standard_type == STANDARD_TYPE_IJARAH:
            print("\n==== IJARAH RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED IJARAH DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END IJARAH FRONTEND DATA ====\n")
        elif standard_type == STANDARD_TYPE_MURABAHA:
            print("\n==== MURABAHA RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED MURABAHA DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END MURABAHA FRONTEND DATA ====\n")
        elif standard_type == STANDARD_TYPE_ISTISNA:
            print("\n==== ISTISNA'A RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED ISTISNA'A DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END ISTISNA'A FRONTEND DATA ====\n")
        elif standard_type == STANDARD_TYPE_SALAM:
            print("\n==== SALAM RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED SALAM DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END SALAM FRONTEND DATA ====\n")
        elif standard_type == STANDARD_TYPE_SUKUK:
            print("\n==== SUKUK RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED SUKUK DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END SUKUK FRONTEND DATA ====\n")
        elif standard_type == STANDARD_TYPE_MUSHARAKA:
            print("\n==== MUSHARAKA RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED MUSHARAKA DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END MUSHARAKA FRONTEND DATA ====\n")
        else:
            print("\n==== GENERIC RESPONSE (FRONTEND) ====\n")
            print(result["response"])
            print("\n==== STRUCTURED DATA (FRONTEND) ====\n")
            print(parsed_result)
            print("\n==== END FRONTEND DATA ====\n")
        
        # Return both the original response and structured data
        response_data = {
            "response": result["response"],
            "thinking_process": thinking_process,
            "explanation": parsed_result.get("explanation", ""),
            "structured_response": parsed_result
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in /usecase: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usecase_bp.route('/validate', methods=['POST'])
def validate_response():
    """Handle validation of a response by the user"""
    data = request.json
    query_text = data.get("query_text")
    response_text = data.get("response_text")
    
    if not query_text or not response_text:
        return jsonify({"error": "Both query_text and response_text are required"}), 400
    
    try:
        # Detect which standard applies to this query
        standard_type = detect_standard_type(query_text)
        
        # Import here to avoid circular import
        from utils.examples import add_example, STANDARD_MAPPINGS
        
        # Add as validated example
        success = add_example(standard_type, query_text, response_text)
        
        if success:
            # Get the standard name for display
            standard_name = STANDARD_MAPPINGS.get(standard_type, "Unknown")
            return jsonify({
                "success": True, 
                "message": f"Response validated and saved as an example for {standard_name}",
                "standard_type": standard_type
            })
        else:
            return jsonify({
                "success": False, 
                "message": "Failed to save validated example"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in /usecase/validate: {str(e)}")
        return jsonify({"error": str(e)}), 500