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
    
    # Build response using a list approach to avoid string formatting issues
    response_parts = []
    
    # Header
    response_parts.append("## ANALYSIS OF IJARAH MBT SCENARIO")
    response_parts.append("")
    response_parts.append("**Transaction Type:** Ijarah Muntahia Bittamleek (Lease ending with ownership)")
    response_parts.append("**Applicable Standard:** AAOIFI FAS 28")
    response_parts.append("**Accounting Method:** Underlying Asset Cost Method")
    response_parts.append("")
    
    # Extracted Variables
    response_parts.append("### EXTRACTED VARIABLES")
    response_parts.append(f"**Purchase Price:** {format_currency(variables.get('purchase_price', 0))}")
    response_parts.append(f"**Import Tax:** {format_currency(variables.get('import_tax', 0))}")
    response_parts.append(f"**Freight Charges:** {format_currency(variables.get('freight_charges', 0))}")
    response_parts.append(f"**Lease Term:** {variables.get('lease_term', 0)} years")
    response_parts.append(f"**Yearly Rental:** {format_currency(variables.get('yearly_rental', 0))}")
    response_parts.append(f"**Residual Value:** {format_currency(variables.get('residual_value', 0))}")
    response_parts.append(f"**Purchase Option Price:** {format_currency(variables.get('purchase_option', 0))}")
    response_parts.append("")
    
    # Calculations
    response_parts.append("### CALCULATIONS")
    response_parts.append("")
    
    # Step 1: Calculate ROU Asset
    response_parts.append("**Step 1: Calculate ROU Asset**")
    response_parts.append(f"Prime Cost = Purchase Price + Import Tax + Freight Charges")
    response_parts.append(f"          = {format_currency(variables.get('purchase_price', 0))} + {format_currency(variables.get('import_tax', 0))} + {format_currency(variables.get('freight_charges', 0))}")
    response_parts.append(f"          = {format_currency(calculations['prime_cost'])}")
    response_parts.append("")
    
    # Step 2: Calculate Deferred Ijarah Cost
    response_parts.append("**Step 2: Calculate Deferred Ijarah Cost**")
    response_parts.append(f"Total Rentals = Yearly Rental × Lease Term")
    response_parts.append(f"              = {format_currency(variables.get('yearly_rental', 0))} × {variables.get('lease_term', 0)}")
    response_parts.append(f"              = {format_currency(calculations['total_rentals'])}")
    response_parts.append("")
    response_parts.append(f"Less ROU Asset = Total Rentals - ROU Asset")
    response_parts.append(f"               = {format_currency(calculations['total_rentals'])} - {format_currency(calculations['rou_asset'])}")
    response_parts.append(f"               = {format_currency(calculations['deferred_cost'])}")
    response_parts.append("")
    
    # Step 3: Calculate Amortizable Amount
    response_parts.append("**Step 3: Calculate Amortizable Amount**")
    response_parts.append(f"ROU Cost = {format_currency(calculations['rou_asset'])}")
    response_parts.append(f"Less Terminal Value Difference = Residual Value - Purchase Option Price")
    response_parts.append(f"                               = {format_currency(variables.get('residual_value', 0))} - {format_currency(variables.get('purchase_option', 0))}")
    response_parts.append(f"                               = {format_currency(calculations['terminal_value_diff'])}")
    response_parts.append(f"Amortizable Amount = ROU Cost - Terminal Value Difference")
    response_parts.append(f"                   = {format_currency(calculations['rou_asset'])} - {format_currency(calculations['terminal_value_diff'])}")
    response_parts.append(f"                   = {format_currency(calculations['amortizable_amount'])}")
    response_parts.append("")
    
    # Journal Entry with Detailed Calculations
    response_parts.append("### JOURNAL ENTRIES WITH CALCULATIONS")
    response_parts.append("")
    
    # Initial Recognition Entry
    response_parts.append("**Initial Recognition:**")
    response_parts.append(f"**Dr.** Right of Use Asset (ROU)         {format_currency(calculations['rou_asset'])}")
    response_parts.append(f"     (= Purchase Price {format_currency(variables.get('purchase_price', 0))} + Import Tax {format_currency(variables.get('import_tax', 0))} + Freight {format_currency(variables.get('freight_charges', 0))})")
    response_parts.append(f"**Dr.** Deferred Ijarah Cost             {format_currency(calculations['deferred_cost'])}")
    response_parts.append(f"     (= Total Rentals {format_currency(calculations['total_rentals'])} - ROU Asset {format_currency(calculations['rou_asset'])})")
    response_parts.append(f"    **Cr.** Ijarah Liability             {format_currency(calculations['ijarah_liability'])}")
    response_parts.append(f"         (= Total Rentals {format_currency(calculations['total_rentals'])})")
    response_parts.append("")
    
    # Amortization Entry (First Period)
    yearly_amortization = calculations['amortizable_amount'] / variables.get('lease_term', 1)
    response_parts.append("**Periodic Amortization (Annual):**")
    response_parts.append(f"**Dr.** Amortization Expense             {format_currency(yearly_amortization)}")
    response_parts.append(f"     (= Amortizable Amount {format_currency(calculations['amortizable_amount'])} ÷ Lease Term {variables.get('lease_term', 0)} years)")
    response_parts.append(f"    **Cr.** Accumulated Amortization      {format_currency(yearly_amortization)}")
    response_parts.append("")
    
    # Rental Payment Entry (First Period)
    yearly_rental = variables.get('yearly_rental', 0)
    yearly_finance_cost = calculations['deferred_cost'] / variables.get('lease_term', 1)
    yearly_liability_reduction = yearly_rental - yearly_finance_cost
    
    response_parts.append("**Periodic Rental Payment (Annual):**")
    response_parts.append(f"**Dr.** Ijarah Liability                {format_currency(yearly_liability_reduction)}")
    response_parts.append(f"**Dr.** Finance Cost                    {format_currency(yearly_finance_cost)}")
    response_parts.append(f"     (= Deferred Cost {format_currency(calculations['deferred_cost'])} ÷ Lease Term {variables.get('lease_term', 0)} years)")
    response_parts.append(f"    **Cr.** Cash/Bank                     {format_currency(yearly_rental)}")
    response_parts.append("")
    
    # Amortizable Amount Calculation
    response_parts.append("### AMORTIZABLE AMOUNT CALCULATION")
    response_parts.append("Description                                               Amount")
    response_parts.append("---|---")
    response_parts.append(f"Cost of ROU                                          {format_currency(calculations['rou_asset'])}")
    response_parts.append(f"Less: Terminal value difference                      {format_currency(calculations['terminal_value_diff'])}")
    response_parts.append(f"       (Residual {format_currency(variables.get('residual_value', 0))} − Purchase {format_currency(variables.get('purchase_option', 0))})    {format_currency(calculations['terminal_value_diff'])}")
    response_parts.append(f"Amortizable Amount                                   {format_currency(calculations['amortizable_amount'])}")
    response_parts.append("")
    
    # Explanation
    response_parts.append("### EXPLANATION")
    response_parts.append("This accounting treatment recognizes:")
    response_parts.append(f"1. The right to use the asset based on its cost minus terminal value ({format_currency(calculations['rou_asset'])})")
    response_parts.append(f"2. The financing cost component ({format_currency(calculations['deferred_cost'])}) to be amortized over the lease term")
    response_parts.append(f"3. The total liability for future lease payments ({format_currency(calculations['ijarah_liability'])})")
    response_parts.append("")
    response_parts.append(f"The amortizable amount of {format_currency(calculations['amortizable_amount'])} reflects the ROU asset adjusted for the value that will remain after ownership transfer. We deduct {format_currency(calculations['terminal_value_diff'])} since the Lessee is expected to gain ownership, and this value will remain in the books after the lease ends.")
    
    # Join all parts with newlines
    response = "\n".join(response_parts)
    
    # Print the response for comparison with frontend
    print("\n==== IJARAH RESPONSE (BACKEND) ====\n")
    print(response)
    print("\n==== END IJARAH RESPONSE ====\n")
    
    return response
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
    
    # Build response using a list approach to avoid string formatting issues
    response_parts = []
    
    # Header
    response_parts.append("## ANALYSIS OF MURABAHA FINANCING")
    response_parts.append("")
    response_parts.append("**Transaction Type:** Murabaha to the Purchase Orderer")
    response_parts.append("**Applicable Standard:** AAOIFI FAS 4")
    response_parts.append("**Accounting Method:** Cost Plus Profit Method")
    response_parts.append("")
    
    # Extracted Variables
    response_parts.append("### EXTRACTED VARIABLES")
    response_parts.append(f"**Cost Price:** {format_currency(variables.get('cost_price', 0))}")
    response_parts.append(f"**Selling Price:** {format_currency(calculations.get('selling_price', 0))}")
    response_parts.append(f"**Profit Rate:** {variables.get('profit_rate', 0)}%")
    response_parts.append(f"**Installments:** {int(variables.get('installments', 1))}")
    response_parts.append(f"**Down Payment:** {format_currency(variables.get('down_payment', 0))}")
    response_parts.append("")
    
    # Calculations
    response_parts.append("### CALCULATIONS")
    response_parts.append("")
    
    # Step 1: Asset Acquisition
    response_parts.append("**Step 1: Asset Acquisition Cost**")
    response_parts.append(f"Asset Cost = {format_currency(variables.get('cost_price', 0))}")
    response_parts.append("")
    
    # Step 2: Murabaha Profit
    response_parts.append("**Step 2: Murabaha Profit Calculation**")
    response_parts.append(f"Selling Price = {format_currency(calculations.get('selling_price', 0))}")
    response_parts.append(f"Cost Price = {format_currency(variables.get('cost_price', 0))}")
    response_parts.append(f"Profit = Selling Price - Cost Price")
    response_parts.append(f"       = {format_currency(calculations.get('selling_price', 0))} - {format_currency(variables.get('cost_price', 0))}")
    response_parts.append(f"       = {format_currency(calculations.get('profit', 0))}")
    response_parts.append("")
    
    # Step 3: Installment Calculation
    response_parts.append("**Step 3: Installment Calculation**")
    response_parts.append(f"Remaining Amount = Selling Price - Down Payment")
    response_parts.append(f"                 = {format_currency(calculations.get('selling_price', 0))} - {format_currency(variables.get('down_payment', 0))}")
    remaining_amount = calculations.get('selling_price', 0) - variables.get('down_payment', 0)
    response_parts.append(f"                 = {format_currency(remaining_amount)}")
    response_parts.append("")
    
    response_parts.append(f"Installment Amount = Remaining Amount ÷ Number of Installments")
    response_parts.append(f"                   = {format_currency(remaining_amount)} ÷ {int(variables.get('installments', 1))}")
    response_parts.append(f"                   = {format_currency(calculations.get('installment_amount', 0))}")
    response_parts.append("")
    
    # Journal Entry with Detailed Calculations
    response_parts.append("### JOURNAL ENTRIES WITH CALCULATIONS")
    response_parts.append("")
    
    # Asset Acquisition Entry
    response_parts.append("**At Asset Acquisition:**")
    response_parts.append(f"**Dr.** Murabaha Asset                   {format_currency(variables.get('cost_price', 0))}")
    response_parts.append(f"    **Cr.** Cash/Bank                    {format_currency(variables.get('cost_price', 0))}")
    response_parts.append("")
    
    # Sale to Customer Entry
    response_parts.append("**At Sale to Customer:**")
    response_parts.append(f"**Dr.** Murabaha Receivables             {format_currency(calculations.get('selling_price', 0))}")
    response_parts.append(f"    **Cr.** Murabaha Asset               {format_currency(variables.get('cost_price', 0))}")
    response_parts.append(f"    **Cr.** Deferred Murabaha Profit     {format_currency(calculations.get('profit', 0))}")
    response_parts.append("")
    
    # Down Payment Entry (if applicable)
    if variables.get('down_payment', 0) > 0:
        response_parts.append("**At Down Payment Receipt:**")
        profit_proportion = variables.get('down_payment', 0) / calculations.get('selling_price', 0)
        profit_recognized = calculations.get('profit', 0) * profit_proportion
        response_parts.append(f"**Dr.** Cash/Bank                       {format_currency(variables.get('down_payment', 0))}")
        response_parts.append(f"    **Cr.** Murabaha Receivables        {format_currency(variables.get('down_payment', 0))}")
        response_parts.append("")
        response_parts.append(f"**Dr.** Deferred Murabaha Profit        {format_currency(profit_recognized)}")
        response_parts.append(f"    **Cr.** Profit Income               {format_currency(profit_recognized)}")
        response_parts.append("")
    
    # Installment Receipt Entry
    response_parts.append("**At Each Installment Receipt:**")
    response_parts.append(f"**Dr.** Cash/Bank                       {format_currency(calculations.get('installment_amount', 0))}")
    response_parts.append(f"    **Cr.** Murabaha Receivables        {format_currency(calculations.get('installment_amount', 0))}")
    response_parts.append("")
    
    profit_per_installment = calculations.get('profit', 0) / variables.get('installments', 1)
    response_parts.append(f"**Dr.** Deferred Murabaha Profit        {format_currency(profit_per_installment)}")
    response_parts.append(f"    **Cr.** Profit Income               {format_currency(profit_per_installment)}")
    response_parts.append("")
    
    # Explanation
    response_parts.append("### EXPLANATION")
    response_parts.append("This accounting treatment:")
    response_parts.append(f"1. Initially recognizes the asset at its acquisition cost ({format_currency(variables.get('cost_price', 0))})")
    response_parts.append(f"2. Upon sale, recognizes the full receivable amount ({format_currency(calculations.get('selling_price', 0))})")
    response_parts.append(f"3. Recognizes the deferred profit ({format_currency(calculations.get('profit', 0))}) to be amortized over the installment period")
    response_parts.append(f"4. Each installment payment will be {format_currency(calculations.get('installment_amount', 0))} and will include both principal recovery and profit recognition")
    response_parts.append("")
    response_parts.append("This accounting treatment follows AAOIFI FAS 4 guidelines for Murabaha financing.")
    
    # Join all parts with newlines
    response = "\n".join(response_parts)
    
    # Print the response for comparison with frontend
    print("\n==== MURABAHA RESPONSE (BACKEND) ====\n")
    print(response)
    print("\n==== END MURABAHA RESPONSE ====\n")
    
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
    
    # Get quarterly progress data if available
    quarterly_progress = calculations.get('quarterly_progress', [])
    
    # Detect if this is a parallel istisna'a scenario
    description = variables.get('description', '').lower()
    is_parallel = 'parallel' in description or 'parallel istisna' in description
    
    # Create the response in a simple way to avoid string formatting issues
    response = []
    
    # Header
    response.append(f"## ANALYSIS OF ISTISNA'A CONTRACT")
    response.append("")
    response.append(f"**Transaction Type:** {'Parallel ' if is_parallel else ''}Istisna'a Contract")
    response.append("**Applicable Standard:** AAOIFI FAS 10")
    response.append("**Accounting Method:** Percentage of Completion Method")
    response.append("")
    
    # Variables section
    response.append("### EXTRACTED VARIABLES")
    for key, value in variables.items():
        # Skip the description field and any non-numeric values
        if key != 'description' and isinstance(value, (int, float)):
            # Format the key for display
            display_key = key.replace('_', ' ').title()
            # Format the value appropriately (currency or number)
            if 'price' in key or 'cost' in key or 'value' in key or 'payment' in key:
                formatted_value = format_currency(value)
            elif 'percentage' in key or 'rate' in key or 'margin' in key:
                formatted_value = format_percentage(value)
            else:
                formatted_value = f"{value}"
            
            response.append(f"**{display_key}:** {formatted_value}")
    response.append("")
    
    # Calculations section
    response.append("### CALCULATIONS")
    
    # Add contract value determination if available
    if 'contract_value' in calculations and 'total_cost' in calculations and 'expected_profit' in calculations:
        response.append("**Contract Value Determination:**")
        response.append(f"- Total Contract Value: {format_currency(calculations['contract_value'])}")
        response.append(f"- Total Cost: {format_currency(calculations['total_cost'])}")
        response.append(f"- Expected Profit: {format_currency(calculations['expected_profit'])}")
        
        if 'profit_margin' in calculations:
            response.append(f"- Profit Margin: {format_percentage(calculations['profit_margin'])}")
        response.append("")
    
    # Add percentage of completion table if quarterly progress is available
    if quarterly_progress:
        response.append("**Percentage of Completion Method:**")
        response.append("")
        response.append("| Period | Cumulative Cost | % Completion | Revenue | Profit | Incremental Revenue | Incremental Profit |")
        response.append("|--------|----------------|--------------|---------|--------|---------------------|-------------------|")
        
        # Add each period's data
        for q in quarterly_progress:
            period = q.get('period', 'N/A')
            cumulative_cost = q.get('cumulative_cost', 0)
            percentage = q.get('percentage_of_completion', 0)
            revenue = q.get('revenue', 0)
            profit = q.get('profit', 0)
            incremental_revenue = q.get('incremental_revenue', 0)
            incremental_profit = q.get('incremental_profit', 0)
            
            response.append(f"| {period} | {format_currency(cumulative_cost)} | {format_percentage(percentage)} | {format_currency(revenue)} | {format_currency(profit)} | {format_currency(incremental_revenue)} | {format_currency(incremental_profit)} |")
        response.append("")
    
    # Journal entries section
    response.append("### JOURNAL ENTRIES")
    
    # Add journal entries for each period if available
    if quarterly_progress:
        for q in quarterly_progress:
            period = q.get('period', 'N/A')
            percentage = q.get('percentage_of_completion', 0)
            cumulative_cost = q.get('cumulative_cost', 0)
            quarterly_cost = q.get('quarterly_cost', 0)
            incremental_revenue = q.get('incremental_revenue', 0)
            incremental_profit = q.get('incremental_profit', 0)
            
            response.append("")
            response.append(f"**{period} - {format_percentage(percentage)} Completion:**")
            response.append("")
            response.append("*Cost Incurred:*")
            response.append(f"**Dr.** Work-in-Progress – Istisna'a     {format_currency(quarterly_cost)}")
            response.append(f"    **Cr.** Bank / Payables              {format_currency(quarterly_cost)}")
            response.append("")
            response.append("*Revenue and Profit Recognition:*")
            response.append(f"**Dr.** Istisna'a Receivable – Client    {format_currency(incremental_revenue)}")
            response.append(f"    **Cr.** Istisna'a Revenue            {format_currency(incremental_revenue)}")
    response.append("")
    
    # Explanation section
    response.append("### EXPLANATION")
    response.append("This accounting treatment follows the percentage-of-completion method as required by AAOIFI FAS 10 for Istisna'a contracts.")
    response.append("")
    
    # Add contract analysis if available
    if 'contract_value' in calculations and 'total_cost' in calculations:
        response.append("**1. Contract Analysis:**")
        for key, value in calculations.items():
            if key in ['contract_value', 'total_cost', 'expected_profit', 'profit_margin']:
                display_key = key.replace('_', ' ').title()
                if key in ['contract_value', 'total_cost', 'expected_profit']:
                    formatted_value = format_currency(value)
                elif key == 'profit_margin':
                    formatted_value = format_percentage(value)
                else:
                    formatted_value = str(value)
                response.append(f"- {display_key}: {formatted_value}")
        response.append("")
    
    # Add quarterly recognition if available
    if len(quarterly_progress) >= 4:
        response.append("**2. Quarterly Recognition:**")
        for i, q in enumerate(quarterly_progress[:4]):
            period = q.get('period', f"Q{i+1}")
            percentage = q.get('percentage_of_completion', 0)
            revenue = q.get('revenue', 0)
            response.append(f"- {period}: {format_percentage(percentage)} completion, recognizing {format_currency(revenue)} revenue")
        response.append("")
    
    # Add accounting principles
    response.append("**3. Accounting Principles:**")
    response.append("- Costs are recorded in Work-in-Progress as incurred")
    response.append("- Revenue is recognized proportionally based on percentage completion")
    response.append("- Profit is recognized in the same proportion as revenue")
    response.append("- Percentage completion is calculated as: Cumulative Cost ÷ Total Estimated Cost")
    response.append("")
    
    # Add final recognition if available
    if 'contract_value' in calculations and 'expected_profit' in calculations and 'total_cost' in calculations:
        response.append("**4. Final Recognition:**")
        response.append(f"- At project completion, the full contract value of {format_currency(calculations['contract_value'])} is recognized")
        response.append(f"- Total profit of {format_currency(calculations['expected_profit'])} is realized")
        response.append(f"- All costs of {format_currency(calculations['total_cost'])} are recorded in the Work-in-Progress account")
    
    # Join all lines with newlines to create the final response
    result = '\n'.join(response)
    
    # Print the response for comparison with frontend
    print("\n==== ISTISNA'A RESPONSE (BACKEND) ====\n")
    print(result)
    print("\n==== END ISTISNA'A RESPONSE ====\n")
    
    return result
