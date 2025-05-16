"""
Formatting utilities for the Islamic Finance API.
"""

def format_ijarah_response(variables, calculations):
    """
    Generate a formatted response for Ijarah scenario based on calculations.
    
    Args:
        variables (dict): The extracted variables
        calculations (dict): The calculated values
        
    Returns:
        str: Formatted response
    """
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
    """
    Generate a formatted response for Murabaha scenario based on calculations.
    
    Args:
        variables (dict): The extracted variables
        calculations (dict): The calculated values
        
    Returns:
        str: Formatted response
    """
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
    """
    Generate a formatted response for Istisna'a scenario based on calculations.
    
    Args:
        variables (dict): The extracted variables
        calculations (dict): The calculated values
        
    Returns:
        str: Formatted response
    """
    def format_currency(value):
        return f"${value:,.2f}"
    
    def format_percentage(value):
        return f"{value:.1f}%"
        
    quarterly_progress = calculations.get('quarterly_progress', [])
    
    # Extract scenario-specific details
    is_parallel = 'parallel' in variables.get('description', '').lower() or len(variables.get('parties', [])) > 2
    payment_terms = variables.get('payment_terms', 'Standard payment terms')
    timeline = variables.get('timeline', 'quarterly')
    
    response = f"""ANALYSIS OF ISTISNA'A CONTRACT
------------------------------
Transaction Type: {'Parallel ' if is_parallel else ''}Istisna'a Contract
Applicable Standard: AAOIFI FAS 10
Accounting Method: Percentage of Completion Method

EXTRACTED VARIABLES
------------------------------
Contract Value: {format_currency(calculations['contract_value'])}
Total Cost: {format_currency(calculations['total_cost'])}
Expected Profit: {format_currency(calculations['expected_profit'])}
Profit Margin: {format_percentage(calculations['profit_margin'])}
Project Timeline: {variables.get('timeline', 'Not specified')}
Payment Structure: {variables.get('payment_terms', 'Not specified')}

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

Step 2: Project Timeline and Payment Structure
  {'This is a Parallel Istisna\'a structure where the bank acts as an intermediary between the client and the contractor.' if is_parallel else 'This is a direct Istisna\'a contract between the bank and the client.'}
  Payment Terms: {payment_terms}

Step 3: {timeline.capitalize()} Progress and Recognition
  Period | Cumulative Cost | % Completion | Revenue | Profit
"""

    for q in quarterly_progress:
        response += f"  {q['quarter']} | {format_currency(q['cumulative_cost'])} | {format_percentage(q['percentage'])} | {format_currency(q['revenue'])} | {format_currency(q['profit'])}\n"
    
    response += f"""
For each period, these detailed calculations are performed:
- Cumulative Cost = Sum of costs incurred up to this period
- Percentage of completion = Cumulative Cost / Total Estimated Cost
  Example for {quarterly_progress[0]['quarter']}: {format_currency(quarterly_progress[0]['cumulative_cost'])} / {format_currency(calculations['total_cost'])} = {format_percentage(quarterly_progress[0]['percentage'])}
- Revenue Recognition = Total Contract Value × Percentage of Completion
  Example for {quarterly_progress[0]['quarter']}: {format_currency(calculations['contract_value'])} × {format_percentage(quarterly_progress[0]['percentage'])} = {format_currency(quarterly_progress[0]['revenue'])}
- Profit Recognition = Total Expected Profit × Percentage of Completion
  Example for {quarterly_progress[0]['quarter']}: {format_currency(calculations['expected_profit'])} × {format_percentage(quarterly_progress[0]['percentage'])} = {format_currency(quarterly_progress[0]['profit'])}

JOURNAL ENTRIES
------------------------------"""

    # Add journal entries for each quarter with more detailed explanations
    for i, q in enumerate(quarterly_progress):
        prev_revenue = 0 if i == 0 else quarterly_progress[i-1]['revenue']
        incremental_revenue = q['revenue'] - prev_revenue
        
        response += f"""
{q['quarter']} - {format_percentage(q['percentage'])} Completion (Cumulative Cost: {format_currency(q['cumulative_cost'])}):

Cost Incurred in this Period:
Dr. Work-in-Progress – Istisna'a     {format_currency(q['quarterly_cost'])}
    Cr. Bank / Payables              {format_currency(q['quarterly_cost'])}
    (Recording actual costs incurred during {q['quarter']})

Revenue and Profit Recognition:
Dr. Istisna'a Receivable – Client    {format_currency(incremental_revenue)}
    Cr. Istisna'a Revenue            {format_currency(incremental_revenue)}
    (Recognizing revenue based on {format_percentage(q['percentage'])} completion, incremental from previous period)

Dr. Istisna'a Cost of Sales          {format_currency(q['quarterly_cost'])}
    Cr. Work-in-Progress             {format_currency(q['quarterly_cost'])}
    (Transferring costs from WIP to Cost of Sales to match revenue recognition)
"""
    
    # Add payment entries with more detailed explanations
    client_payment_schedule = variables.get('client_payment_schedule', [])
    contractor_payment_schedule = variables.get('contractor_payment_schedule', [])
    
    if client_payment_schedule:
        response += "\nClient Payment Entries:\n"
        for payment in client_payment_schedule:
            response += f"""At {payment.get('timing', 'payment date')}:
Dr. Bank / Cash                     {format_currency(payment.get('amount', 0))}
    Cr. Istisna'a Receivable        {format_currency(payment.get('amount', 0))}
    (Receipt of client payment as per contract terms)\n\n"""
    else:
        # Use default payment structure if specific schedule not provided
        payment_amount = calculations['contract_value']/4
        response += f"""\nUpon Receipt of Each Client Payment ({format_currency(payment_amount)}):
Dr. Bank / Cash                     {format_currency(payment_amount)}
    Cr. Istisna'a Receivable        {format_currency(payment_amount)}
    (Receipt of client payment as per contract terms)\n\n"""
    
    if contractor_payment_schedule and is_parallel:
        response += "\nContractor Payment Entries (Parallel Istisna'a):\n"
        for payment in contractor_payment_schedule:
            response += f"""At {payment.get('timing', 'payment date')}:
Dr. Payables to Contractor          {format_currency(payment.get('amount', 0))}
    Cr. Bank / Cash                 {format_currency(payment.get('amount', 0))}
    (Payment to contractor as per parallel Istisna'a contract)\n\n"""
    
    # Add summary ledger section
    total_cost = calculations['total_cost']
    total_revenue = calculations['contract_value']
    total_profit = calculations['expected_profit']
    
    response += f"""
EXPLANATION
------------------------------
This accounting treatment for {'Parallel ' if is_parallel else ''}Istisna'a contracts follows the percentage-of-completion method as required by AAOIFI FAS 10. The method recognizes revenue, expenses, and profit gradually as the construction progresses, providing a fair representation of the financial activity over the contract period.

Key aspects of this accounting treatment:
1. Revenue and profit are recognized progressively based on the percentage of completion
2. The percentage of completion is measured by comparing costs incurred to date with total estimated costs
3. This approach aligns with AAOIFI FAS 10 paragraph 8, which states that "revenue and profit shall be recognized according to the percentage of completion method"
4. For parallel Istisna'a, the bank acts as an intermediary, earning profit from the difference between the two contracts

The bank's total profit of {format_currency(calculations['expected_profit'])} represents the difference between the contract value with the client ({format_currency(calculations['contract_value'])}) and the cost from the contractor ({format_currency(calculations['total_cost'])}). This profit is recognized over the project duration based on completion percentage.

SUMMARY LEDGER
------------------------------
Work-in-Progress Account:
Opening Balance: $0.00
"""

    # Add WIP account details
    wip_debits = sum(q['quarterly_cost'] for q in quarterly_progress)
    response += f"Debits (Total): {format_currency(wip_debits)} (Costs incurred)\n"
    response += f"Credits (Total): {format_currency(wip_debits)} (Transfer to Cost of Sales)\n"
    response += "Closing Balance: $0.00\n\n"
    
    # Add Istisna'a Receivable account details
    response += "Istisna'a Receivable Account:\n"
    response += "Opening Balance: $0.00\n"
    response += f"Debits (Total): {format_currency(total_revenue)} (Revenue recognized)\n"
    response += f"Credits (Total): {format_currency(total_revenue)} (Client payments)\n"
    response += "Closing Balance: $0.00\n\n"
    
    # Add Istisna'a Revenue account details
    response += "Istisna'a Revenue Account:\n"
    response += "Opening Balance: $0.00\n"
    response += f"Credits (Total): {format_currency(total_revenue)} (Revenue recognized)\n"
    response += f"Closing Balance: {format_currency(total_revenue)} (Credit)\n\n"
    
    # Add Istisna'a Cost of Sales account details
    response += "Istisna'a Cost of Sales Account:\n"
    response += "Opening Balance: $0.00\n"
    response += f"Debits (Total): {format_currency(total_cost)} (Costs transferred from WIP)\n"
    response += f"Closing Balance: {format_currency(total_cost)} (Debit)\n\n"
    
    # Add Profit summary
    response += f"Net Profit: {format_currency(total_profit)} (Revenue {format_currency(total_revenue)} - Cost {format_currency(total_cost)})\n"""
    
    
    return response
