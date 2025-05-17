from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from analyzer import IslamicFinanceMultiAgentAnalyzer

# Load environment variables
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Initialize analyzer
analyzer = IslamicFinanceMultiAgentAnalyzer(api_key=GEMINI_API_KEY)

# Create Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r'/*': {'origins': '*'}})

@app.route('/api/analyze', methods=['POST'])
def analyze_transaction():
    """
    Endpoint to analyze Islamic finance transactions
    
    Expects JSON with:
    - 'text': String containing the transaction text to analyze
    - 'transaction_name' (optional): Name of the transaction
    
    Returns JSON with analysis results from the multi-agent system
    """
    # Get JSON data from request
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({
            'error': 'Missing required parameter: text'
        }), 400
    
    # Get parameters
    transaction_text = data['text']
    transaction_name = data.get('transaction_name', 'Unnamed Transaction')
    
    try:
        # Run the analysis
        result = analyzer.run_multi_agent_analysis(transaction_text)
        
        # Return formatted response
        response = {
            'transaction_name': transaction_name,
            'primary_standard': result.get('primary_standard', 'Unknown'),
            'confidence': result.get('confidence', 0),
            'consensus_level': result.get('consensus_level', 0),
            'applicable_standards': result.get('applicable_standards', []),
            'agent_votes': result.get('agent_votes', {}),
            'standard_confidence': result.get('standard_confidence', {}),
            'anomalies': result.get('anomalies', []),
            'detailed_justification': result.get('detailed_justification', ''),
        }
        
        # Include optional sections if available
        if 'ambiguity_analysis' in result:
            response['ambiguity_analysis'] = result['ambiguity_analysis']
            
        if 'clarification' in result:
            response['clarification'] = result['clarification']
            
        if 'arabic_analysis' in result:
            response['arabic_analysis'] = result['arabic_analysis']
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/reversetransaction', methods=['POST'])
def reverse_transaction():
    """
    Endpoint to analyze Islamic finance transactions from the frontend
    
    Expects JSON with:
    - 'query_text': String containing the transaction text to analyze
    
    Returns JSON with analysis results from the multi-agent system
    """
    # Get JSON data from request
    data = request.get_json()
    
    if not data or 'query_text' not in data:
        return jsonify({
            'error': 'Missing required parameter: query_text'
        }), 400
    
    # Get parameters
    transaction_text = data['query_text']
    transaction_name = data.get('transaction_name', 'Unnamed Transaction')
    
    try:
        # Run the analysis
        result = analyzer.run_multi_agent_analysis(transaction_text)
        
        # Return formatted response
        response = {
            'transaction_name': transaction_name,
            'primary_standard': result.get('primary_standard', 'Unknown'),
            'primary_sharia_standard': result.get('primary_standard', 'Unknown'),  # Added for frontend compatibility
            'confidence': result.get('confidence', 0),
            'consensus_level': result.get('consensus_level', 0),
            'applicable_standards': result.get('applicable_standards', []),
            'agent_votes': result.get('agent_votes', {}),
            'standard_confidence': result.get('standard_confidence', {}),
            'anomalies': result.get('anomalies', []),
            'detailed_justification': result.get('detailed_justification', ''),
            'thinking_process': []  # Added for frontend compatibility
        }
        
        # Include optional sections if available
        if 'ambiguity_analysis' in result:
            response['ambiguity_analysis'] = result['ambiguity_analysis']
            
        if 'clarification' in result:
            response['clarification'] = result['clarification']
            
        if 'arabic_analysis' in result:
            response['arabic_analysis'] = result['arabic_analysis']
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Islamic Finance Analyzer API'})

if __name__ == '__main__':
    app.run(debug=True, port=5002)