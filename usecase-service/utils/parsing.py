"""
Parsing utilities for the Islamic Finance API.
"""

import re

def extract_thinking_process(response_text):
    """
    Extract thinking process from response if available.
    
    Args:
        response_text (str): The response text to extract thinking process from
        
    Returns:
        str or None: The extracted thinking process if available, None otherwise
    """
    thinking_match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
    if thinking_match:
        return thinking_match.group(1).strip()
    return None

def parse_financial_data(response_text, query_text):
    """
    Parse structured financial data from the response text.
    
    Args:
        response_text (str): The response text to parse
        query_text (str): The original query text
        
    Returns:
        dict: Parsed financial data
    """
    result = {
        "explanation": "",
        "calculations": [],
        "journal_entries": [],
        "ledger_summary": [],
        "amortizable_amount_table": []
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
        (r"(?:Less: Terminal value|Less Terminal value).*?=[\s]*([0-9,.]+)[\s]*[-−][\s]*([0-9,.]+)[\s]*=[\s]*([0-9,.]+)[\s]*\(ROU\)", 
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
    
    # Extract amortizable amount calculation table for Ijarah
    if "ijarah" in query_text.lower() or "lease" in query_text.lower():
        amortizable_table_match = re.search(r"AMORTIZABLE AMOUNT CALCULATION\s*\n.*?\n.*?\n(.*?)(?:\n\n|\n[A-Z]|\Z)", response_text, re.DOTALL)
        if amortizable_table_match:
            table_rows = amortizable_table_match.group(1).strip().split('\n')
            for row in table_rows:
                # Extract description and amount
                parts = row.split()
                if len(parts) >= 2:
                    # Last part is the amount
                    amount_str = parts[-1].replace(',', '').replace('$', '')
                    try:
                        amount = float(amount_str)
                        # Join all parts except the last one as the description
                        description = ' '.join(parts[:-1])
                        result["amortizable_amount_table"].append({
                            "description": description,
                            "amount": amount
                        })
                    except ValueError:
                        # Skip if amount is not a valid number
                        pass

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
