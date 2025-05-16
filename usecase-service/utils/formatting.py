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

**Transaction Type:** Ijarah Muntahia Bittamleek (Lease ending with ownership)  
**Applicable Standard:** AAOIFI FAS 28  
**Accounting Method:** Underlying Asset Cost Method  

### EXTRACTED VARIABLES
**Purchase Price:** {format_currency(variables.get('purchase_price', 0))}  
**Import Tax:** {format_currency(variables.get('import_tax', 0))}  
**Freight Charges:** {format_currency(variables.get('freight_charges', 0))}  
**Lease Term:** {variables.get('lease_term', 0)} years  
**Yearly Rental:** {format_currency(variables.get('yearly_rental', 0))}  
**Residual Value:** {format_currency(variables.get('residual_value', 0))}  
**Purchase Option Price:** {format_currency(variables.get('purchase_option', 0))}  

### CALCULATIONS
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
**Dr.** Right of Use Asset (ROU)         {format_currency(calculations['rou_asset'])}  
**Dr.** Deferred Ijarah Cost             {format_currency(calculations['deferred_cost'])}  
    **Cr.** Ijarah Liability             {format_currency(calculations['ijarah_liability'])}  

### AMORTIZABLE AMOUNT CALCULATION
Description                                               Amount
---|---
Cost of ROU                                          {format_currency(calculations['rou_asset'])}
Less: Terminal value difference                      {format_currency(calculations['terminal_value_diff'])}
       (Residual {format_currency(variables.get('residual_value', 0))} − Purchase {format_currency(variables.get('purchase_option', 0))})    {format_currency(calculations['terminal_value_diff'])}
Amortizable Amount                                   {format_currency(calculations['amortizable_amount'])}

### EXPLANATION
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
    response = f"""## ANALYSIS OF MURABAHA FINANCING

**Transaction Type:** Murabaha to the Purchase Orderer  
**Applicable Standard:** AAOIFI FAS 4  
**Accounting Method:** Cost Plus Profit Method  

### EXTRACTED VARIABLES
**Cost Price:** {format_currency(variables.get('cost_price', 0))}  
**Selling Price:** {format_currency(calculations.get('selling_price', 0))}  
**Profit Rate:** {variables.get('profit_rate', 0)}%  
**Installments:** {int(variables.get('installments', 1))}  
**Down Payment:** {format_currency(variables.get('down_payment', 0))}  

### CALCULATIONS

Initial Recognition:
Step 1: Asset Acquisition Cost = {format_currency(variables.get('cost_price', 0))}
Step 2: Murabaha Profit = {format_currency(calculations.get('profit', 0))}
Step 3: Installment Amount = {format_currency(calculations.get('installment_amount', 0))}

### JOURNAL ENTRY
At Asset Acquisition:
**Dr.** Murabaha Asset                   {format_currency(variables.get('cost_price', 0))}  
    **Cr.** Cash/Bank                    {format_currency(variables.get('cost_price', 0))}  

At Sale to Customer:
**Dr.** Murabaha Receivables             {format_currency(calculations.get('selling_price', 0))}  
    **Cr.** Murabaha Asset               {format_currency(variables.get('cost_price', 0))}  
    **Cr.** Deferred Murabaha Profit     {format_currency(calculations.get('profit', 0))}  

### EXPLANATION
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
    
    response = f"""## ANALYSIS OF ISTISNA'A CONTRACT

**Transaction Type:** {'Parallel ' if is_parallel else ''}Istisna'a Contract  
**Applicable Standard:** AAOIFI FAS 10  
**Accounting Method:** Percentage of Completion Method  

### EXTRACTED VARIABLES
**Contract Value:** {format_currency(calculations['contract_value'])}  
**Total Cost:** {format_currency(calculations['total_cost'])}  
**Expected Profit:** {format_currency(calculations['expected_profit'])}  
**Profit Margin:** {format_percentage(calculations['profit_margin'])}  
**Project Timeline:** {variables.get('timeline', 'Not specified')}  
**Payment Structure:** {variables.get('payment_terms', 'Not specified')}  

### CALCULATIONS
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
  This is a {'Parallel ' if is_parallel else ''}Istisna'a structure where the bank acts as an intermediary between the client and the contractor.
  Payment Terms: {payment_terms}

Step 3: {timeline.capitalize()} Progress and Recognition
  
  Period | Cumulative Cost | % Completion | Revenue | Profit
  -------|----------------|--------------|---------|-------
"""

    # Add quarterly progress data
    for q in quarterly_progress:
        quarter = q['quarter']
        percentage = q['percentage']
        cumulative_cost = q['cumulative_cost']
        revenue = q['revenue']
        profit = q['profit']
        
        response += f"  {quarter} | {format_currency(cumulative_cost)} | {percentage}% | {format_currency(revenue)} | {format_currency(profit)}\n"
    
    # Add journal entries section
    response += f"""
### JOURNAL ENTRIES
"""

    # Add journal entries for each quarter
    for q in quarterly_progress:
        quarter = q['quarter']
        quarterly_cost = q['quarterly_cost']
        incremental_revenue = q['incremental_revenue']
        
        response += f"""
{quarter} - {q['percentage']}% Completion (Cumulative Cost: {format_currency(q['cumulative_cost'])}):

Cost Incurred:
**Dr.** Work-in-Progress – Istisna'a     {format_currency(quarterly_cost)}
    **Cr.** Bank / Payables              {format_currency(quarterly_cost)}

Revenue and Profit Recognition:
**Dr.** Istisna'a Receivable – Client    {format_currency(incremental_revenue)}
    **Cr.** Istisna'a Revenue            {format_currency(incremental_revenue)}
"""

    # Add explanation section
    response += f"""
### EXPLANATION
This accounting treatment follows the percentage-of-completion method as required by AAOIFI FAS 10:

1. The total contract value is {format_currency(calculations['contract_value'])}, with an expected profit of {format_currency(calculations['expected_profit'])} (profit margin: {format_percentage(calculations['profit_margin'])})

2. As construction progresses, we recognize:
   - Costs incurred in the Work-in-Progress account
   - Revenue and receivables based on the percentage of completion
   - Profit proportionate to the work completed

3. The percentage of completion is determined by comparing cumulative costs incurred to total estimated costs.

4. At completion (100%), the full contract value will be recognized as revenue, and all costs will be recorded in the Work-in-Progress account.
"""

    return response
