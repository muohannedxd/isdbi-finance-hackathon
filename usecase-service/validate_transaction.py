import os
import json
import sys
import re
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables (for OpenAI API key)
load_dotenv()

def generate_reverse_transaction(response_data):
    """Generate a true reverse transaction based on the original journal entries"""
    
    # Extract transaction type from the response
    if "MURABAHA FINANCING" in response_data:
        transaction_type = "Murabaha"
    elif "IJARAH MBT SCENARIO" in response_data:
        transaction_type = "Ijarah"
    elif "SALAM CONTRACT" in response_data:
        transaction_type = "Salam"
    elif "ISTISNA'A CONTRACT" in response_data:
        transaction_type = "Istisna'a"
    elif "SUKUK TRANSACTION" in response_data:
        transaction_type = "Sukuk"
    else:
        transaction_type = "Unknown"
    
    # Extract the original applicable standard
    original_standard = None
    if "Applicable Standard:" in response_data:
        standard_line = re.search(r'Applicable Standard:.*?([^\n]+)', response_data)
        if standard_line:
            original_standard = standard_line.group(1).strip()
    
    # Extract journal entries from response
    original_entries = []
    reversed_entries = []
    
    if "JOURNAL ENTRY" in response_data:
        journal_section = response_data.split("JOURNAL ENTRY")[1]
        # Handle case where there might not be an EXPLANATION section
        if "EXPLANATION" in journal_section:
            journal_section = journal_section.split("EXPLANATION")[0]
        
        # Clean up and extract entries
        entries = journal_section.strip().split("\n")
        
        for entry in entries:
            entry = entry.strip()
            if "Dr." in entry:
                # Found a debit entry, add to original and create reversed credit entry
                original_entries.append(entry)
                
                # Parse account name and amount
                account_match = re.search(r'Dr\.\s+(.*?)\s+(\$[\d,]+)', entry)
                if account_match:
                    account = account_match.group(1).strip()
                    amount = account_match.group(2).strip()
                    reversed_entries.append(f"Cr. {account}{' ' * (30 - len(account))}{amount}")
                
            elif "Cr." in entry:
                # Found a credit entry, add to original and create reversed debit entry
                original_entries.append(entry)
                
                # Parse account name and amount
                account_match = re.search(r'Cr\.\s+(.*?)\s+(\$[\d,]+)', entry)
                if account_match:
                    account = account_match.group(1).strip()
                    amount = account_match.group(2).strip()
                    reversed_entries.append(f"Dr. {account}{' ' * (30 - len(account))}{amount}")
    
    # Format transaction details for output
    transaction_date = "Year 3"  # Assuming this from context
    transaction_description = f"Reversal of {transaction_type} transaction"
    
    # Create reverse transaction format
    reverse_transaction = f"""Reverse Transaction for {transaction_type}
Transaction Date: {transaction_date}
Transaction Description: {transaction_description}

ORIGINAL JOURNAL ENTRIES:
------------------------------
{chr(10).join(original_entries)}

REVERSE JOURNAL ENTRIES:
------------------------------
{chr(10).join(reversed_entries)}

Original Transaction Type: {transaction_type}
Original Applicable Standard: {original_standard}
"""
    return reverse_transaction, original_standard

def validate_with_llm(reverse_transaction):
    """Use LLM to validate which AAOIFI FAS standards apply to the transaction"""
    
    prompt = f"""You are an Islamic finance accounting expert. Review this transaction and determine 
which AAOIFI FAS standards are applicable to the REVERSE JOURNAL ENTRIES.

{reverse_transaction}

Challenge: 
Can you identify the AAOIFI FAS applicable to the REVERSE JOURNAL ENTRIES? If more than one is possible, 
include weighted probability and reason for each.

Your answer should be structured as follows:
1. Primary applicable FAS: [standard number] - [probability]% - [reason]
2. Secondary applicable FAS: [standard number] - [probability]% - [reason]
3. Tertiary applicable FAS: [standard number] - [probability]% - [reason]

Be objective and thorough in your analysis. Do not be influenced by the Original Applicable Standard - 
evaluate the REVERSE JOURNAL ENTRIES independently.
"""

    try:
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,
        )
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error validating with LLM: {str(e)}"

def extract_fas_standards(validation_result):
    """Extract FAS standards and their weights from the validation result"""
    standards = []
    # Look for patterns like "FAS 4 - 70%" or "FAS 4 (70%)" or similar formats
    fas_pattern = r"FAS\s+(\d+).*?(\d+)%"
    matches = re.findall(fas_pattern, validation_result)
    
    for match in matches:
        standard_num = match[0]
        weight = int(match[1])
        standards.append({
            "standard": f"FAS {standard_num}",
            "weight": weight
        })
    
    # Sort by weight in descending order
    standards.sort(key=lambda x: x["weight"], reverse=True)
    return standards

def assess_response(validation_result, original_standard):
    """Assess if the LLM validation matches the original standard used"""
    result = "VALIDATION ASSESSMENT:\n"
    
    # Extract the standards and their weights from the LLM's response
    extracted_standards = extract_fas_standards(validation_result)
    
    if not extracted_standards:
        return result + "❌ ERROR: Could not parse standards and weights from the validation result.\n"
    
    # Get the highest weighted standard from LLM
    highest_standard = extracted_standards[0]["standard"] if extracted_standards else None
    
    # Format the standards and weights for display
    standards_list = "\n".join([f"- {s['standard']}: {s['weight']}%" for s in extracted_standards])
    result += f"Standards by weight:\n{standards_list}\n\n"
    
    # Extract just the number from standards for comparison
    original_standard_num = None
    if original_standard:
        fas_match = re.search(r'FAS\s+(\d+)', original_standard)
        if fas_match:
            original_standard_num = f"FAS {fas_match.group(1)}"
    
    # Check if the highest weighted standard matches the original standard number
    if highest_standard and original_standard_num and highest_standard == original_standard_num:
        result += f"✅ MATCH: Highest weighted standard ({highest_standard}) matches the original standard ({original_standard_num}).\n"
    elif highest_standard and original_standard_num:
        result += f"❌ MISMATCH: Highest weighted standard ({highest_standard}) does not match the original standard ({original_standard_num}).\n"
    elif highest_standard and original_standard:
        if highest_standard in original_standard:
            result += f"✅ MATCH: Highest weighted standard ({highest_standard}) found in original standard description ({original_standard}).\n"
        else:
            result += f"❌ MISMATCH: Highest weighted standard ({highest_standard}) not found in original standard description ({original_standard}).\n"
    else:
        result += "⚠️ INCONCLUSIVE: Could not determine if standards match.\n"
    
    # Additional detailed analysis of other standards
    if len(extracted_standards) > 1:
        result += f"\nSecondary applicable standards:\n"
        for std in extracted_standards[1:]:
            result += f"- {std['standard']}: {std['weight']}%\n"
    
    return result

def main(query_output=None):
    """Main function to process the output and generate validation"""
    
    if not query_output:
        print("Please provide the output from query_data.py")
        return
    
    # Generate reverse transaction and extract original standard
    reverse_transaction, original_standard = generate_reverse_transaction(query_output)
    print("\n" + "="*60)
    print("GENERATED REVERSE TRANSACTION:")
    print("="*60)
    print(reverse_transaction)
    
    # Validate with LLM
    print("\n" + "="*60)
    print("VALIDATING WITH LLM...")
    print("="*60)
    validation_result = validate_with_llm(reverse_transaction)
    print(validation_result)
    
    # Assess the validation result
    print("\n" + "="*60)
    print(assess_response(validation_result, original_standard))
    print("="*60)

if __name__ == "__main__":
    # If output is passed as command line argument
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as file:
                query_output = file.read()
            main(query_output)
        except FileNotFoundError:
            print(f"Error: File {sys.argv[1]} not found.")
    else:
        # For testing, you can replace this with sample output
        sample_output = """
ANALYSIS OF MURABAHA FINANCING
------------------------------
Transaction Type: Murabaha to the Purchase Orderer
Applicable Standard: AAOIFI FAS 4
Accounting Method: Cost Plus Profit Method

EXTRACTED VARIABLES
------------------------------
Cost Price: $100,000
Selling Price: $110,000
Profit Rate: 10%
Installments: 12
Down Payment: $10,000

JOURNAL ENTRY
------------------------------
At Asset Acquisition:
Dr. Murabaha Asset                   $100,000
    Cr. Cash/Bank                    $100,000

At Sale to Customer:
Dr. Murabaha Receivables             $110,000
    Cr. Murabaha Asset               $100,000
    Cr. Deferred Murabaha Profit     $10,000

EXPLANATION
------------------------------
This accounting treatment follows AAOIFI FAS 4 guidelines for Murabaha financing.
"""
        main(sample_output)