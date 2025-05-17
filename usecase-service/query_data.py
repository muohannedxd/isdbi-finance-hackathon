from flask import Flask, request, jsonify
import os
import json
import re
import io
import sys
import time
import pickle
import logging
from datetime import datetime
from langdetect import detect
from langchain_together import ChatTogether
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_together import ChatTogether
from dotenv import load_dotenv
import pickle
import hashlib

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Add CORS support to allow requests from frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Import API method from constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from isdb_backend.utils.constants import API_METHOD, GEMINI_MODEL

CHROMA_PATH = "chroma"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
TOGETHER_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
DEFAULT_LLM_MODEL = GEMINI_MODEL if API_METHOD == "gemini" else TOGETHER_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("islamic_finance_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("islamic_finance_api")

# Standards information
STANDARDS_INFO = """
FAS 4: Musharaka Financing
This standard prescribes the accounting rules for recognition, measurement, presentation, and disclosure of Musharaka financing transactions for Islamic financial institutions. Musharaka is a form of partnership between the Islamic bank and its clients whereby each party contributes to the capital of partnership in equal or varying degrees to establish a new project or share in an existing one, and whereby each of the parties becomes an owner of the capital on a permanent or declining basis and has a due share of profits. Losses are shared in proportion to the contributed capital. The standard covers both constant and diminishing Musharaka arrangements.

FAS 7: Salam and Parallel Salam
This standard addresses the accounting treatment for Salam and Parallel Salam transactions. Salam is a sale whereby the seller undertakes to supply a specific commodity to the buyer at a future date in exchange for an advanced price fully paid at spot. The standard covers the accounting by Islamic banks for funds disbursed in a Salam contract as well as the goods received under a Salam contract. It also addresses parallel Salam transactions where an Islamic bank enters into a second Salam contract to acquire goods of similar specifications to fulfill its obligation in the first Salam contract.

FAS 10: Istisna'a and Parallel Istisna'a
This standard prescribes the accounting rules for Istisna'a and parallel Istisna'a transactions for Islamic financial institutions. Istisna'a is a sale contract between a buyer (customer) and a manufacturer/seller, whereby the manufacturer/seller undertakes to manufacture and deliver a specified item, at an agreed price, on a specified future date. The standard covers the accounting treatment for Istisna'a contracts including revenue recognition, cost allocation, and disclosure requirements. It also addresses parallel Istisna'a where an Islamic bank enters into a second Istisna'a contract to fulfill its obligation in the first contract.

FAS 28: Murabaha and Other Deferred Payment Sales
This standard prescribes the accounting rules for recognition, measurement, presentation, and disclosure of Murabaha and other deferred payment sales transactions for Islamic financial institutions. Murabaha is a sale of goods at cost plus an agreed profit margin. The standard covers various types of Murabaha transactions including the traditional Murabaha and Murabaha to the purchase orderer (MPO). It addresses issues such as initial recognition, subsequent measurement, profit recognition, deferred payment, early settlement discounts, and default scenarios. This standard supersedes the earlier FAS 2.

FAS 32: Ijarah and Ijarah Muntahia Bittamleek
This standard establishes the principles of classification, recognition, measurement, presentation, and disclosure for Ijarah (lease) transactions including their different forms entered into by Islamic financial institutions in both capacities as lessor and lessee. It covers operating Ijarah, Ijarah Muntahia Bittamleek (lease ending with ownership transfer), and sublease transactions. The standard addresses the accounting treatment for right-of-use assets, lease liabilities, subsequent measurement, modifications, and other related aspects. This standard supersedes the earlier FAS 8.

FAS 30: Impairment, Credit Losses and Onerous Commitments
This standard establishes the principles for the recognition, measurement, and disclosure of impairment and credit losses for various Islamic financing and investment assets, as well as provisions against onerous commitments. It introduces an expected credit loss approach for impairment assessment with a forward-looking 'expected loss' model. The standard covers financial assets and commitments exposed to credit risk, with specific guidance for different types of Islamic financing contracts.

FAS 35: Risk Reserves
This standard prescribes the accounting principles for risk reserves established to mitigate various risks faced by stakeholders, particularly profit and loss taking investors, of Islamic financial institutions. It covers the establishment and utilization of two main types of risk reserves: Profit Equalization Reserve (PER) and Investment Risk Reserve (IRR). The standard addresses when these reserves should be recognized, how they should be measured, and the required disclosures.

Related Shari'a Standards (SS):
SS 9: Ijarah and Ijarah Muntahia Bittamleek
SS 8: Murabaha
SS 11: Istisna'a and Parallel Istisna'a 
SS 10: Salam and Parallel Salam 
SS 12: Sharikah (Musharakah) and Modern Corporations
SS 5: Guarantees
This standard defines the Shari'a principles for various types of guarantees including personal guarantees (kafala), pledges (rahn), and performance bonds in Islamic financial transactions. It outlines permissible and impermissible forms of security arrangements, conditions for their validity, and guidelines for charging fees on guarantee services.

SS 17: Investment Sukuk
This standard defines the characteristics and types of investment sukuk, including their issuance, trading, and redemption according to Shari'a principles. It covers various structures such as Ijarah Sukuk, Musharakah Sukuk, Mudarabah Sukuk, and others, with specific rules for each type regarding underlying assets, ownership transfer, tradability, and profit distribution.

SS 13: Mudarabah
This standard outlines the Shari'a rules for Mudarabah (profit-sharing) financing arrangements where one party provides capital and another party provides entrepreneurial skills. It covers capital conditions, profit distribution mechanisms, termination procedures, and restrictions on the activities of the mudarib (entrepreneur).
"""

def detect_language(text):
    """Detect the language of the transaction text."""
    try:
        detected_lang = detect(text)
        return detected_lang
    except:
        logger.warning("Language detection failed, defaulting to English")
        return 'en'

def detect_anomalies(result, transaction_text):
    """Detect anomalies in the analysis."""
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

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

STANDARD_TYPE_MURABAHA = "MURABAHA"
STANDARD_TYPE_SALAM = "SALAM"
STANDARD_TYPE_ISTISNA = "ISTISNA"
STANDARD_TYPE_IJARAH = "IJARAH"
STANDARD_TYPE_SUKUK = "SUKUK"

MURABAHA_PROMPT_TEMPLATE = """
You are an Islamic finance accounting specialist. Analyze the following Murabaha financing scenario and provide structured accounting analysis according to AAOIFI FAS 4.

CONTEXT FROM ISLAMIC FINANCE STANDARDS:
{context}

SCENARIO:
{question}

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
ANALYSIS OF MURABAHA FINANCING
------------------------------
Transaction Type: Murabaha to the Purchase Orderer
Applicable Standard: AAOIFI FAS 4
Accounting Method: Cost Plus Profit Method

EXTRACTED VARIABLES
------------------------------
[List all monetary values, terms, and relevant financial data extracted from the scenario]

CALCULATIONS
------------------------------
Initial Recognition:
Step 1: Asset Acquisition Cost
Step 2: Murabaha Profit Calculation
Step 3: Installment/Deferred Payment Calculation

JOURNAL ENTRY
------------------------------
[Format proper accounting journal entries with clear debits and credits]

EXPLANATION
------------------------------
[Provide concise explanation of the accounting treatment and its compliance with Islamic finance principles]
"""

SALAM_PROMPT_TEMPLATE = """
You are an Islamic finance accounting specialist. Analyze the following Salam contract scenario and provide structured accounting analysis according to AAOIFI FAS 7.

CONTEXT FROM ISLAMIC FINANCE STANDARDS:
{context}

SCENARIO:
{question}

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
ANALYSIS OF SALAM CONTRACT
------------------------------
Transaction Type: Salam Contract
Applicable Standard: AAOIFI FAS 7
Accounting Method: Cost Method

EXTRACTED VARIABLES
------------------------------
[List all monetary values, terms, and relevant financial data extracted from the scenario]

CALCULATIONS
------------------------------
Initial Recognition:
Step 1: Salam Capital Recognition
Step 2: Salam Asset Recognition
Step 3: Profit/Loss Calculation (if applicable)

JOURNAL ENTRY
------------------------------
[Format proper accounting journal entries with clear debits and credits]

EXPLANATION
------------------------------
[Provide concise explanation of the accounting treatment and its compliance with Islamic finance principles]
"""

ISTISNA_PROMPT_TEMPLATE = """
You are an Islamic finance accounting specialist. Analyze the following Istisna'a contract scenario and provide structured accounting analysis according to AAOIFI FAS 10.

CONTEXT FROM ISLAMIC FINANCE STANDARDS:
{context}

SCENARIO:
{question}

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
ANALYSIS OF ISTISNA'A CONTRACT
------------------------------
Transaction Type: Istisna'a Contract
Applicable Standard: AAOIFI FAS 10
Accounting Method: Percentage of Completion Method

EXTRACTED VARIABLES
------------------------------
[List all monetary values, terms, and relevant financial data extracted from the scenario]

CALCULATIONS
------------------------------
Step 1: Contract Value Determination
  Total Contract Value = [Amount]
  Total Cost = [Amount]
  Total Expected Profit = [Amount]
  Profit Margin = [Percentage]

Step 2: Quarterly Progress and Recognition
  Quarter | Cumulative Cost | % Completion | Revenue | Profit
  Q1 | [Amount] | [Percentage] | [Amount] | [Amount]
  Q2 | [Amount] | [Percentage] | [Amount] | [Amount]
  Q3 | [Amount] | [Percentage] | [Amount] | [Amount]
  Q4 | [Amount] | [Percentage] | [Amount] | [Amount]

For each quarter, show the detailed calculation of:
- Percentage of completion = Cumulative Cost / Total Estimated Cost
- Revenue = Total Contract Value × Percentage of Completion
- Profit = Total Expected Profit × Percentage of Completion

JOURNAL ENTRY
------------------------------
For Quarter 1 (25% Completion):
Dr. Work-in-Progress – Istisna'a [Amount]
Cr. Bank/Payables [Amount]

Dr. Istisna'a Receivable [Amount]
Cr. Istisna'a Revenue [Amount]

Dr. Istisna'a Cost of Sales [Amount]
Cr. Work-in-Progress [Amount]

[Repeat for other quarters as needed]

EXPLANATION
------------------------------
[Provide concise explanation of the accounting treatment and its compliance with Islamic finance principles, focusing on how percentage-of-completion method aligns with FAS 10]
"""

IJARAH_PROMPT_TEMPLATE = """
You are an Islamic finance accounting specialist. Analyze the following Ijarah Muntahia Bittamleek (lease ending with ownership) scenario and provide structured accounting analysis.

CONTEXT FROM ISLAMIC FINANCE STANDARDS:
{context}

SCENARIO:
{question}

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
ANALYSIS OF IJARAH MBT SCENARIO
------------------------------
Transaction Type: Ijarah Muntahia Bittamleek (Lease ending with ownership)
Applicable Standard: AAOIFI FAS 28
Accounting Method: Underlying Asset Cost Method

EXTRACTED VARIABLES
------------------------------
[List all monetary values, terms, and relevant financial data extracted from the scenario]

CALCULATIONS
------------------------------
Initial Recognition at the Time of Commencement of Ijarah:
Step 1: Calculate ROU Asset
  Prime Cost = Purchase Price + Import Tax + Freight Charges
  Less Terminal Value = Prime Cost - Purchase Option Price

Step 2: Calculate Deferred Ijarah Cost
  Total Rentals = Yearly Rental × Lease Term
  Less ROU Asset = Total Rentals - ROU Asset

Step 3: Calculate Amortizable Amount
  ROU Cost = [Value calculated in Step 1]
  Less Terminal Value Difference = Residual Value - Purchase Option Price
  Amortizable Amount = ROU Cost - Terminal Value Difference

JOURNAL ENTRY
------------------------------
Dr. Right of Use Asset (ROU)         [Amount]
Dr. Deferred Ijarah Cost             [Amount]
    Cr. Ijarah Liability             [Amount]

EXPLANATION
------------------------------
[Explain that the entry recognizes the right to use the asset based on its cost minus terminal value, the financing cost component to be amortized over the lease term, and the total liability for future lease payments. Also explain that the amortizable amount reflects the ROU asset adjusted for the value that will remain after ownership transfer.]
"""

SUKUK_PROMPT_TEMPLATE = """
You are an Islamic finance accounting specialist. Analyze the following Sukuk issuance or investment scenario and provide structured accounting analysis according to AAOIFI FAS 32.

CONTEXT FROM ISLAMIC FINANCE STANDARDS:
{context}

SCENARIO:
{question}

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
ANALYSIS OF SUKUK TRANSACTION
------------------------------
Transaction Type: [Sukuk Issuance/Investment]
Applicable Standard: AAOIFI FAS 32
Classification: [Monetary Asset/Non-monetary Asset/Hybrid]

EXTRACTED VARIABLES
------------------------------
[List all monetary values, terms, and relevant financial data extracted from the scenario]

CALCULATIONS
------------------------------
Initial Recognition:
Step 1: Classification of Sukuk
Step 2: Valuation Method
Step 3: Profit/Return Calculation

JOURNAL ENTRY
------------------------------
[Format proper accounting journal entries with clear debits and credits]

EXPLANATION
------------------------------
[Provide concise explanation of the accounting treatment and its compliance with Islamic finance principles]
"""

def analyze_transaction(transaction_text, model=None, temperature=0.2):
    """Analyze a transaction using the configured LLM API (Gemini or Together AI) via LangChain."""
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

def get_cached_response(prompt, cache_file="response_cache.pkl"):
    """Get cached response if it exists"""
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
    """Cache the response for future use"""
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    try:
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
    except (FileNotFoundError, EOFError):
        cache = {}
    cache[prompt_hash] = response
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)

def detect_standard_type(query_text):
    """Detect which AAOIFI standard applies to the scenario"""
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
    """Extract key financial variables from an Ijarah scenario text using regex"""
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
    """Extract key financial variables from a Murabaha scenario text using regex"""
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
    """Extract key financial variables from an Istisna'a contract scenario text using regex"""
    patterns = {
        'contract_value': r'(?:price|contract value|agreed price|contract amount).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'total_cost': r'(?:cost|total cost|estimated cost|contractor.*?cost).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'delivery_period': r'(?:delivery|completion|construction).*?([0-9,.]+)[\s]*(?:month|months|year|years)',
        'installments': r'(?:installment|payment).*?([0-9]+)[\s]*(?:quarterly|monthly|annual|installment)',
        'upfront_payment': r'(?:upfront|advance|initial).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)',
        'completion_payment': r'(?:completion|final).*?(?:\$|USD|usd|SAR|sar|AED|aed|EUR|eur|GBP|gbp)[,\s]*([0-9,.]+)'
    }
    
    extracted_values = {}
    
    # Try specialized patterns first for common payment structures
    # Check for specifically formatted price and cost in the use case format
    price_match = re.search(r'[Pp]rice:? \$?([0-9,.]+)', query_text)
    if price_match:
        extracted_values['contract_value'] = float(price_match.group(1).replace(',', ''))
    
    cost_match = re.search(r'[Cc]ost:? \$?([0-9,.]+)', query_text)
    if cost_match:
        extracted_values['total_cost'] = float(cost_match.group(1).replace(',', ''))
    
    # Look for payment structures in the specific format used in the use case
    payment_match = re.search(r'([0-9,.]+) upfront, ([0-9,.]+) on completion', query_text)
    if payment_match:
        extracted_values['upfront_payment'] = float(payment_match.group(1).replace(',', ''))
        extracted_values['completion_payment'] = float(payment_match.group(2).replace(',', ''))
    
    # Check for dollar amounts with $ prefix
    dollar_amounts = re.findall(r'\$([0-9,.]+)', query_text)
    if len(dollar_amounts) >= 2 and 'contract_value' not in extracted_values:
        for i, amount in enumerate(dollar_amounts):
            if i == 0 and 'contract_value' not in extracted_values:
                # First $ amount is often the contract value
                extracted_values['contract_value'] = float(amount.replace(',', ''))
            elif i == 1 and 'total_cost' not in extracted_values:
                # Second $ amount is often the cost
                extracted_values['total_cost'] = float(amount.replace(',', ''))
    
    # Then try the general patterns for any remaining values
    for key, pattern in patterns.items():
        if key not in extracted_values:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    extracted_values[key] = float(value_str)
                except ValueError:
                    pass
    
    # Handle specific formats for upfront and completion payments
    upfront_completion_match = re.search(r'\$([0-9,.]+) upfront, \$([0-9,.]+) on completion', query_text)
    if upfront_completion_match and 'upfront_payment' not in extracted_values:
        extracted_values['upfront_payment'] = float(upfront_completion_match.group(1).replace(',', ''))
        extracted_values['completion_payment'] = float(upfront_completion_match.group(2).replace(',', ''))
    
    # Special case for the parallel Istisna'a use case with specific payment terms 
    payment_structure_match = re.search(r'Payment: ([0-9,.]+) ([a-zA-Z]+), ([0-9,.]+) ([a-zA-Z]+)', query_text)
    if payment_structure_match:
        amount1 = float(payment_structure_match.group(1).replace(',', ''))
        term1 = payment_structure_match.group(2).lower()
        amount2 = float(payment_structure_match.group(3).replace(',', ''))
        term2 = payment_structure_match.group(4).lower()
        
        if 'upfront' in term1 or 'advance' in term1:
            extracted_values['upfront_payment'] = amount1
        elif 'completion' in term1 or 'final' in term1:
            extracted_values['completion_payment'] = amount1
            
        if 'upfront' in term2 or 'advance' in term2:
            extracted_values['upfront_payment'] = amount2
        elif 'completion' in term2 or 'final' in term2:
            extracted_values['completion_payment'] = amount2
    
    # If we found contract value and total cost but no payment structure,
    # try to infer the payment structure from the context
    if 'contract_value' in extracted_values and 'total_cost' in extracted_values:
        if 'upfront_payment' not in extracted_values and 'completion_payment' not in extracted_values:
            # Check for specific mentions of payment structure
            if re.search(r'upfront.*?completion', query_text, re.IGNORECASE):
                # If we find a mention of upfront and completion payments without amounts,
                # assume a 50/50 split for the total cost
                extracted_values['upfront_payment'] = extracted_values['total_cost'] / 2
                extracted_values['completion_payment'] = extracted_values['total_cost'] / 2
    
    return extracted_values

def calculate_ijarah_values(variables):
    """Calculate Ijarah accounting values based on extracted variables"""
    results = {}
    purchase_price = variables.get('purchase_price', 0)
    import_tax = variables.get('import_tax', 0)
    freight_charges = variables.get('freight_charges', 0)
    yearly_rental = variables.get('yearly_rental', 0)
    lease_term = variables.get('lease_term', 0)
    residual_value = variables.get('residual_value', 0)
    purchase_option = variables.get('purchase_option', 0)
    prime_cost = purchase_price + import_tax + freight_charges
    rou_asset = prime_cost - purchase_option
    total_rentals = yearly_rental * lease_term
    deferred_cost = total_rentals - rou_asset
    terminal_value_diff = residual_value - purchase_option
    amortizable_amount = rou_asset - terminal_value_diff
    results['prime_cost'] = prime_cost
    results['rou_asset'] = rou_asset
    results['total_rentals'] = total_rentals
    results['deferred_cost'] = deferred_cost
    results['terminal_value_diff'] = terminal_value_diff
    results['amortizable_amount'] = amortizable_amount
    results['ijarah_liability'] = total_rentals
    return results

def calculate_murabaha_values(variables):
    """Calculate Murabaha accounting values based on extracted variables"""
    results = {}
    cost_price = variables.get('cost_price', 0)
    selling_price = variables.get('selling_price', 0)
    profit_rate = variables.get('profit_rate', 0)
    installments = variables.get('installments', 1)
    down_payment = variables.get('down_payment', 0)
    if selling_price == 0 and cost_price > 0 and profit_rate > 0:
        selling_price = cost_price * (1 + profit_rate/100)
        results['selling_price'] = selling_price
    if selling_price > 0 and cost_price > 0:
        profit = selling_price - cost_price
        results['profit'] = profit
        if installments > 0:
            remaining_amount = selling_price - down_payment
            installment_amount = remaining_amount / installments
            results['installment_amount'] = installment_amount
    results['cost_price'] = cost_price
    results['selling_price'] = selling_price
    results['profit'] = results.get('profit', 0)
    results['installment_amount'] = results.get('installment_amount', 0)
    return results

def calculate_istisna_values(variables):
    """Calculate Istisna'a accounting values based on extracted variables"""
    results = {}
    contract_value = variables.get('contract_value', 0)
    total_cost = variables.get('total_cost', 0)
    delivery_period = variables.get('delivery_period', 12)  # Default to 12 months if not specified
    installments = variables.get('installments', 4)  # Default to 4 installments

    # Calculate expected profit
    expected_profit = contract_value - total_cost
    profit_margin = (expected_profit / contract_value) * 100 if contract_value > 0 else 0
    
    results['contract_value'] = contract_value
    results['total_cost'] = total_cost
    results['expected_profit'] = expected_profit
    results['profit_margin'] = profit_margin
    
    # Calculate quarterly progress (assuming 4 equal quarters)
    quarterly_results = []
    for i in range(1, 5):
        percentage = i * 25  # Q1=25%, Q2=50%, Q3=75%, Q4=100%
        
        # Calculate based on even distribution across quarters
        quarterly_cost = total_cost / 4  # Cost per quarter
        cumulative_cost = quarterly_cost * i  # Cumulative cost through this quarter
        
        # Calculate revenue and profit based on percentage of completion
        quarterly_revenue = contract_value * (percentage / 100)
        quarterly_profit = expected_profit * (percentage / 100)
        
        # For incremental calculations
        incremental_revenue = contract_value * 0.25  # 25% per quarter
        incremental_profit = expected_profit * 0.25  # 25% per quarter
        
        quarterly_results.append({
            'quarter': f"Q{i}",
            'percentage': percentage,
            'cumulative_cost': cumulative_cost,
            'quarterly_cost': quarterly_cost,
            'revenue': quarterly_revenue,
            'profit': quarterly_profit,
            'incremental_revenue': incremental_revenue,
            'incremental_profit': incremental_profit
        })
    
    results['quarterly_progress'] = quarterly_results
    return results

def format_ijarah_response(variables, calculations):
    """Generate a formatted response for Ijarah scenario based on calculations"""
    def format_currency(value):
        return f"${value:,.2f}"
    response = f"""## ANALYSIS OF IJARAH MBT SCENARIO
------------------------------
**Transaction Type:** Ijarah Muntahia Bittamleek (Lease ending with ownership)  
**Applicable Standard:** AAOIFI FAS 28  
**Accounting Method:** Underlying Asset Cost Method  

### EXTRACTED VARIABLES
------------------------------
**Purchase Price:** {format_currency(variables.get('purchase_price', 0))}  
**Import Tax:** {format_currency(variables.get('import_tax', 0))}  
**Freight Charges:** {format_currency(variables.get('freight_charges', 0))}  
**Lease Term:** {variables.get('lease_term', 0)} years  
**Yearly Rental:** {format_currency(variables.get('yearly_rental', 0))}  
**Residual Value:** {format_currency(variables.get('residual_value', 0))}  
**Purchase Option Price:** {format_currency(variables.get('purchase_option', 0))}  

### CALCULATIONS
------------------------------
<think>
Step 1: Calculate ROU Asset
Prime Cost = Purchase Price + Import Tax + Freight Charges
          = {format_currency(variables.get('purchase_price', 0))} + {format_currency(variables.get('import_tax', 0))} + {format_currency(variables.get('freight_charges', 0))} 
          = {format_currency(calculations['prime_cost'])}
          
Less Terminal Value = Prime Cost - Purchase Option Price
                    = {format_currency(calculations['prime_cost'])} - {format_currency(variables.get('purchase_option', 0))}
                    = {format_currency(calculations['rou_asset'])}

Step 2: Calculate Deferred Ijarah Cost
Total Rentals = Yearly Rental × Lease Term
              = {format_currency(variables.get('yearly_rental', 0))} × {variables.get('lease_term', 0)}
              = {format_currency(calculations['total_rentals'])}
              
Less ROU Asset = Total Rentals - ROU Asset
               = {format_currency(calculations['total_rentals'])} - {format_currency(calculations['rou_asset'])}
               = {format_currency(calculations['deferred_cost'])}

Step 3: Calculate Amortizable Amount
ROU Cost = {format_currency(calculations['rou_asset'])}
Less Terminal Value Difference = Residual Value - Purchase Option Price
                               = {format_currency(variables.get('residual_value', 0))} - {format_currency(variables.get('purchase_option', 0))}
                               = {format_currency(calculations['terminal_value_diff'])}
Amortizable Amount = ROU Cost - Terminal Value Difference
                   = {format_currency(calculations['rou_asset'])} - {format_currency(calculations['terminal_value_diff'])}
                   = {format_currency(calculations['amortizable_amount'])}
</think>

### JOURNAL ENTRY
------------------------------
**Dr.** Right of Use Asset (ROU)         {format_currency(calculations['rou_asset'])}  
**Dr.** Deferred Ijarah Cost             {format_currency(calculations['deferred_cost'])}  
    **Cr.** Ijarah Liability             {format_currency(calculations['ijarah_liability'])}  

### AMORTIZABLE AMOUNT CALCULATION
------------------------------
Description                                               Amount
---|---
Cost of ROU                                          {format_currency(calculations['rou_asset'])}
Less: Terminal value difference                      {format_currency(calculations['terminal_value_diff'])}
       (Residual {format_currency(variables.get('residual_value', 0))} − Purchase {format_currency(variables.get('purchase_option', 0))})    {format_currency(calculations['terminal_value_diff'])}
Amortizable Amount                                   {format_currency(calculations['amortizable_amount'])}

### EXPLANATION
------------------------------
This entry recognizes:
1. The right to use the asset based on its cost minus terminal value ({format_currency(calculations['rou_asset'])})
2. The financing cost component ({format_currency(calculations['deferred_cost'])}) to be amortized over the lease term
3. The total liability for future lease payments ({format_currency(calculations['ijarah_liability'])})

The amortizable amount of {format_currency(calculations['amortizable_amount'])} reflects the ROU asset adjusted for the value that will remain after ownership transfer. We deduct {format_currency(calculations['terminal_value_diff'])} since the Lessee is expected to gain ownership, and this value will remain in the books after the lease ends.
"""
    return response

def format_murabaha_response(variables, calculations):
    """Generate a formatted response for Murabaha scenario based on calculations"""
    def format_currency(value):
        return f"${value:,.2f}"
    response = f"""ANALYSIS OF MURABAHA FINANCING
------------------------------
Transaction Type: Murabaha to the Purchase Orderer
Applicable Standard: AAOIFI FAS 4
Accounting Method: Cost Plus Profit Method

EXTRACTED VARIABLES
------------------------------
Cost Price: {format_currency(variables.get('cost_price', 0))}
Selling Price: {format_currency(calculations.get('selling_price', 0))}
Profit Rate: {variables.get('profit_rate', 0)}%
Installments: {int(variables.get('installments', 1))}
Down Payment: {format_currency(variables.get('down_payment', 0))}

CALCULATIONS
------------------------------
Initial Recognition:
Step 1: Asset Acquisition Cost = {format_currency(variables.get('cost_price', 0))}
Step 2: Murabaha Profit = {format_currency(calculations.get('profit', 0))}
Step 3: Installment Amount = {format_currency(calculations.get('installment_amount', 0))}

JOURNAL ENTRY
------------------------------
At Asset Acquisition:
Dr. Murabaha Asset                   {format_currency(variables.get('cost_price', 0))}
    Cr. Cash/Bank                    {format_currency(variables.get('cost_price', 0))}

At Sale to Customer:
Dr. Murabaha Receivables             {format_currency(calculations.get('selling_price', 0))}
    Cr. Murabaha Asset               {format_currency(variables.get('cost_price', 0))}
    Cr. Deferred Murabaha Profit     {format_currency(calculations.get('profit', 0))}

EXPLANATION
------------------------------
This accounting treatment:
1. Initially recognizes the asset at its acquisition cost ({format_currency(variables.get('cost_price', 0))})
2. Upon sale, recognizes the full receivable amount ({format_currency(calculations.get('selling_price', 0))})
3. Recognizes the deferred profit ({format_currency(calculations.get('profit', 0))}) to be amortized over the installment period
4. Each installment payment will be {format_currency(calculations.get('installment_amount', 0))} and will include both principal recovery and profit recognition
"""
    return response

def format_istisna_response(variables, calculations):
    """Generate a formatted response for Istisna'a scenario based on calculations"""
    def format_currency(value):
        return f"${value:,.2f}"
    
    def format_percentage(value):
        return f"{value:.1f}%"
        
    quarterly_progress = calculations.get('quarterly_progress', [])
    
    response = f"""ANALYSIS OF ISTISNA'A CONTRACT
------------------------------
Transaction Type: Istisna'a Contract
Applicable Standard: AAOIFI FAS 10
Accounting Method: Percentage of Completion Method

EXTRACTED VARIABLES
------------------------------
Contract Value: {format_currency(calculations['contract_value'])}
Total Cost: {format_currency(calculations['total_cost'])}
Expected Profit: {format_currency(calculations['expected_profit'])}
Profit Margin: {format_percentage(calculations['profit_margin'])}

CALCULATIONS
------------------------------
Step 1: Contract Value Determination
  Total Contract Value = {format_currency(calculations['contract_value'])}
  Total Cost = {format_currency(calculations['total_cost'])}
  Total Expected Profit = Total Contract Value - Total Cost
                       = {format_currency(calculations['contract_value'])} - {format_currency(calculations['total_cost'])}
                       = {format_currency(calculations['expected_profit'])}
  Profit Margin = Expected Profit / Contract Value × 100%
                = {format_currency(calculations['expected_profit'])} / {format_currency(calculations['contract_value'])} × 100%
                = {format_percentage(calculations['profit_margin'])}

Step 2: Quarterly Progress and Recognition
  Quarter | Cumulative Cost | % Completion | Revenue | Profit
"""

    for q in quarterly_progress:
        response += f"  {q['quarter']} | {format_currency(q['cumulative_cost'])} | {format_percentage(q['percentage'])} | {format_currency(q['revenue'])} | {format_currency(q['profit'])}\n"
    
    response += f"""
For each quarter, the calculation follows:
- Percentage of completion = Cumulative Cost / Total Estimated Cost
- Revenue = Total Contract Value × Percentage of Completion
- Profit = Total Expected Profit × Percentage of Completion

JOURNAL ENTRIES
------------------------------"""

    # Add journal entries for each quarter
    for i, q in enumerate(quarterly_progress):
        response += f"""
{q['quarter']} - {format_percentage(q['percentage'])} Completion (Cumulative Cost: {format_currency(q['cumulative_cost'])})

Cost Incurred:
Dr. Work-in-Progress – Istisna'a     {format_currency(q['quarterly_cost'])}
    Cr. Bank / Payables              {format_currency(q['quarterly_cost'])}

Revenue and Profit Recognition:
Dr. Istisna'a Receivable – Client    {format_currency(q['revenue'] if i == 0 else q['incremental_revenue'])}
    Cr. Istisna'a Revenue            {format_currency(q['revenue'] if i == 0 else q['incremental_revenue'])}

Dr. Istisna'a Cost of Sales          {format_currency(q['quarterly_cost'])}
    Cr. Work-in-Progress             {format_currency(q['quarterly_cost'])}
"""
    
    # Add payment entry
    payment_amount = calculations['contract_value']/4
    response += f"""
Upon Receipt of Each Client Payment ({format_currency(payment_amount)}):
Dr. Bank / Cash                     {format_currency(payment_amount)}
    Cr. Istisna'a Receivable        {format_currency(payment_amount)}

EXPLANATION
------------------------------
This accounting treatment for Istisna'a contracts follows the percentage-of-completion method as required by AAOIFI FAS 10. The method recognizes revenue, expenses, and profit gradually as the construction progresses, providing a fair representation of the financial activity over the contract period.

For each quarter, we recognize:
1. The cost incurred in that period as Work-in-Progress
2. Revenue proportional to the percentage of completion 
3. Profit proportional to the percentage of completion

The bank's total profit of {format_currency(calculations['expected_profit'])} represents the difference between the contract value with the client ({format_currency(calculations['contract_value'])}) and the cost from the contractor ({format_currency(calculations['total_cost'])}). This profit is recognized over the project duration based on completion percentage.
"""
    
    return response

def get_prompt_for_standard(standard_type):
    """Get the appropriate prompt template for the detected standard"""
    if standard_type == STANDARD_TYPE_MURABAHA:
        return MURABAHA_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_SALAM:
        return SALAM_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_ISTISNA:
        return ISTISNA_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_IJARAH:
        return IJARAH_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_SUKUK:
        return SUKUK_PROMPT_TEMPLATE
    else:
        return PROMPT_TEMPLATE

def process_query(query_text, embedding_model=DEFAULT_EMBEDDING_MODEL, llm_model=None, use_openai=False, force_reload=False):
    """Process a query and return the response using the configured LLM API (Gemini or Together AI) via LangChain."""
    
    # Set default model based on API_METHOD if none provided
    if llm_model is None:
        llm_model = TOGETHER_MODEL if API_METHOD == "together" else GEMINI_MODEL
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
    elif standard_type == STANDARD_TYPE_ISTISNA and "percentage" in query_text.lower():
        variables = extract_istisna_variables(query_text)
        if 'contract_value' in variables and 'total_cost' in variables:
            calculations = calculate_istisna_values(variables)
            response_text = format_istisna_response(variables, calculations)
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
        
    results = db.similarity_search_with_relevance_scores(search_query, k=5)
    if len(results) == 0 or results[0][1] < -9:
        raise ValueError("Unable to find matching results.")
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(get_prompt_for_standard(standard_type))
    prompt = prompt_template.format(context=context_text, question=query_text)
    cached_response = get_cached_response(prompt)
    if cached_response and not force_reload:
        response_text = cached_response
    else:
        llm = ChatTogether(
            model=llm_model,
            temperature=0.3,
            together_api_key=os.getenv("TOGETHER_API_KEY")
        )
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        cache_response(prompt, response_text)
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    return {"response": response_text, "sources": sources}


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/usecase', methods=['POST'])
def query():
    data = request.json
    query_text = data.get("query_text")
    embedding_model = data.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    llm_model = data.get("llm_model", TOGETHER_MODEL)
    use_openai = data.get("use_openai", True)
    force_reload = data.get("force_reload", False)
    
    if not query_text:
        return jsonify({"error": "query_text is required"}), 400
    
    try:
        # Process the query as before
        result = process_query(query_text, embedding_model, llm_model, use_openai, force_reload)
        
        # Extract thinking process if present
        thinking_process = extract_thinking_process(result["response"])
        
        # Parse the response to extract structured financial data
        parsed_result = parse_financial_data(result["response"], query_text)
        
        # Return both the original response and structured data
        return jsonify({
            "response": result["response"],
            "thinking_process": thinking_process,
            "explanation": parsed_result.get("explanation", ""),
            "structured_response": parsed_result
        })
    except Exception as e:
        logger.error(f"Error in /usecase: {str(e)}")
        return jsonify({"error": str(e)}), 500

def extract_thinking_process(response_text):
    """Extract thinking process from response if available"""
    thinking_match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if thinking_match:
        return thinking_match.group(1).strip()
    return None

def parse_financial_data(response_text, query_text):
    """Parse structured financial data from the response text"""
    result = {
        "explanation": "",
        "calculations": [],
        "journal_entries": [],
        "ledger_summary": []
    }
    
    # Extract explanation
    explanation_match = re.search(r"EXPLANATION[\s\-]*\n(.*?)(?:\n\n|\n[A-Z]|\Z)", response_text, re.DOTALL)
    if not explanation_match:
        explanation_match = re.search(r"(?:Initial Recognition|ANALYSIS)[\s\-]*.*?\n(.*?)(?:Determine|Journal|JOURNAL|CALCULATIONS)", response_text, re.DOTALL)
    
    if explanation_match:
        result["explanation"] = explanation_match.group(1).strip()
    else:
        # If no specific explanation section, use first paragraph
        paragraphs = response_text.split("\n\n")
        if paragraphs:
            result["explanation"] = paragraphs[0].strip()
    
    # Extract calculations
    calculation_patterns = [
        # Pattern for ROU asset calculation
        (r"(?:Prime cost|Purchase \+ Import tax \+ Freight)[:\s].*?([0-9,.]+)[\s]*\+[\s]*([0-9,.]+)[\s]*\+[\s]*([0-9,.]+)[\s]*=[\s]*([0-9,.]+)", 
         lambda m: {"label": "Prime Cost", "value": float(m.group(4).replace(',', ''))}),
        (r"(?:Less: Terminal value|Less Terminal value).*?=[\s]*([0-9,.]+)[\s]*[-−][\s]*([0-9,.]+)[\s]*=[\s]*([0-9,.]+)", 
         lambda m: {"label": "ROU Asset", "value": float(m.group(3).replace(',', ''))}),
        (r"Total rentals over[\s]*([0-9]+)[\s]*years?[\s]*=[\s]*([0-9,.]+)[\s]*[×x][\s]*([0-9]+)[\s]*=[\s]*([0-9,.]+)", 
         lambda m: {"label": "Total Rentals", "value": float(m.group(4).replace(',', ''))}),
        (r"Deferred Ijarah Cost[\s]*=[\s]*([0-9,.]+)[\s]*[-−][\s]*([0-9,.]+)[\s]*=[\s]*([0-9,.]+)", 
         lambda m: {"label": "Deferred Ijarah Cost", "value": float(m.group(3).replace(',', ''))}),
        (r"Terminal value difference[\s]*[\(\[]?.*?[\)\]]?[\s]*=[\s]*([0-9,.]+)[\s]*[-−][\s]*([0-9,.]+)[\s]*=[\s]*([0-9,.]+)", 
         lambda m: {"label": "Terminal Value Difference", "value": float(m.group(3).replace(',', ''))}),
        (r"Amortizable Amount[\s]*=[\s]*([0-9,.]+)[\s]*[-−][\s]*([0-9,.]+)[\s]*=[\s]*([0-9,.]+)", 
         lambda m: {"label": "Amortizable Amount", "value": float(m.group(3).replace(',', ''))}),
        # Pattern for Istisna'a profit calculation
        (r"Profit[\s]*=[\s]*\$?([0-9,.]+)[\s]*[-−][\s]*\$?([0-9,.]+)[\s]*=[\s]*\$?([0-9,.]+)", 
         lambda m: {"label": "Profit", "value": float(m.group(3).replace(',', ''))}),
    ]
    
    for pattern, process_func in calculation_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                result["calculations"].append(process_func(re.search(pattern, response_text, re.IGNORECASE)))
            else:
                for match in matches:
                    if isinstance(match, str):
                        # Handle single group matches differently
                        continue
                    result["calculations"].append(process_func(re.search(pattern, response_text, re.IGNORECASE)))
    
    # Extract percentage of completion data for Istisna'a contracts
    if "istisna" in query_text.lower() and "percentage" in query_text.lower():
        # Find the table with percentage of completion data
        poc_table_match = re.search(r"Quarter[\s\t]*Cumulative Cost[\s\t]*%[\s\t]*Completion.*?\n(.*?)(?:\n\n|\Z)", response_text, re.DOTALL)
        if poc_table_match:
            table_rows = poc_table_match.group(1).strip().split('\n')
            for row in table_rows:
                # Extract quarter, cost, completion percentage, and profit
                match = re.search(r"Q([1-4])[\s\t]*\$?([0-9,.]+)[\s\t]*([0-9,.]+)%?[\s\t]*\$?([0-9,.]+)", row.replace(' ', ''))
                if match:
                    quarter = match.group(1)
                    cost = float(match.group(2).replace(',', ''))
                    percentage = float(match.group(3))
                    profit = float(match.group(4).replace(',', ''))
                    
                    result["calculations"].append({"label": f"Q{quarter} Cost", "value": cost})
                    result["calculations"].append({"label": f"Q{quarter} Completion", "value": percentage})
                    result["calculations"].append({"label": f"Q{quarter} Profit", "value": profit})
        
        # Extract quarterly accounting entries and build ledger summary
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        ledger_data = []
        
        for q in quarters:
            work_in_progress = 0
            receivable = 0
            revenue = 0
            cost_of_sales = 0
            profit = 0
            bank_payable = 0
            
            # Find cost entries
            cost_match = re.search(rf"{q}.*?Cost.*?\$([0-9,.]+)", response_text, re.IGNORECASE)
            if cost_match:
                work_in_progress = float(cost_match.group(1).replace(',', ''))
                cost_of_sales = work_in_progress
                bank_payable = work_in_progress
            
            # Find revenue entries
            revenue_match = re.search(rf"{q}.*?Revenue.*?\$([0-9,.]+)", response_text, re.IGNORECASE)
            if revenue_match:
                revenue = float(revenue_match.group(1).replace(',', ''))
                receivable = revenue
            
            # Find profit entries
            profit_match = re.search(rf"{q}.*?Profit.*?\$([0-9,.]+)", response_text, re.IGNORECASE)
            if profit_match:
                profit = float(profit_match.group(1).replace(',', ''))
            
            if work_in_progress > 0 or receivable > 0:
                ledger_data.append({
                    "Quarter": q,
                    "Work-in-Progress": work_in_progress,
                    "Receivable": receivable,
                    "Revenue": revenue,
                    "Cost of Sales": cost_of_sales,
                    "Profit": profit,
                    "Bank/Payables": bank_payable,
                })
        
        # Add payment entries if they exist
        payment_entries = []
        for i in range(1, 5):
            payment_match = re.search(rf"Payment {i}.*?(?:Bank|Cash).*?\$([0-9,.]+)", response_text, re.IGNORECASE)
            if payment_match:
                amount = float(payment_match.group(1).replace(',', ''))
                payment_entries.append({
                    "Quarter": f"Payment {i}",
                    "Work-in-Progress": 0,
                    "Receivable": -amount,
                    "Revenue": 0,
                    "Cost of Sales": 0,
                    "Profit": 0,
                    "Bank/Payables": 0,
                    "Cash Received": amount
                })
        
        # Add payment entries to ledger summary
        ledger_data.extend(payment_entries)
        
        # Calculate totals
        if ledger_data:
            totals = {
                "Quarter": "Total",
                "Work-in-Progress": sum(row.get("Work-in-Progress", 0) for row in ledger_data),
                "Receivable": sum(row.get("Receivable", 0) for row in ledger_data),
                "Revenue": sum(row.get("Revenue", 0) for row in ledger_data),
                "Cost of Sales": sum(row.get("Cost of Sales", 0) for row in ledger_data),
                "Profit": sum(row.get("Profit", 0) for row in ledger_data),
                "Bank/Payables": sum(row.get("Bank/Payables", 0) for row in ledger_data),
                "Cash Received": sum(row.get("Cash Received", 0) for row in ledger_data if "Cash Received" in row)
            }
            ledger_data.append(totals)
            
        result["ledger_summary"] = ledger_data
    
    # Extract journal entries
    journal_section_match = re.search(r"Journal Entry:?\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)", response_text, re.DOTALL)
    if journal_section_match:
        journal_text = journal_section_match.group(1)
        dr_entries = re.findall(r"Dr\.?\s+(.*?)\s*(?:USD|$|\(ROU\))\s*\$?([0-9,.]+)", journal_text, re.IGNORECASE)
        cr_entries = re.findall(r"Cr\.?\s+(.*?)\s*(?:USD|$)\s*\$?([0-9,.]+)", journal_text, re.IGNORECASE)
        
        for account, amount_str in dr_entries:
            amount = float(amount_str.replace(',', ''))
            result["journal_entries"].append({
                "debit": account.strip(),
                "amount": amount
            })
        
        for account, amount_str in cr_entries:
            amount = float(amount_str.replace(',', ''))
            result["journal_entries"].append({
                "credit": account.strip(),
                "amount": amount
            })
    
    # If there are no journal entries found through the Journal Entry section, look for entries throughout the text
    if not result["journal_entries"]:
        all_dr_entries = re.findall(r"Dr\.?\s+(.*?)\s*\$?([0-9,.]+)", response_text, re.IGNORECASE)
        all_cr_entries = re.findall(r"Cr\.?\s+(.*?)\s*\$?([0-9,.]+)", response_text, re.IGNORECASE)
        
        # Group related entries together
        entry_sets = []
        current_set = []
        
        for i, entry in enumerate(all_dr_entries + all_cr_entries):
            if i > 0 and entry[0].strip().lower().startswith(('dr.', 'cr.')):
                entry_sets.append(current_set)
                current_set = []
            current_set.append(entry)
        
        if current_set:
            entry_sets.append(current_set)
        
        # Use the first set of entries if multiple sets exist
        if entry_sets:
            first_set = entry_sets[0]
            for account, amount_str in first_set:
                amount = float(amount_str.replace(',', ''))
                is_debit = account.strip().lower().startswith('dr.')
                
                if is_debit:
                    result["journal_entries"].append({
                        "debit": account.replace('Dr.', '').strip(),
                        "amount": amount
                    })
                else:
                    result["journal_entries"].append({
                        "credit": account.replace('Cr.', '').strip(),
                        "amount": amount
                    })
    
    return result