"""
Calculation utilities for the Islamic Finance API.
"""

def calculate_ijarah_values(variables):
    """
    Calculate Ijarah accounting values based on extracted variables.
    
    Args:
        variables (dict): The extracted variables
        
    Returns:
        dict: Calculated values
    """
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
    """
    Calculate Murabaha accounting values based on extracted variables.
    
    Args:
        variables (dict): The extracted variables
        
    Returns:
        dict: Calculated values
    """
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
    """
    Calculate Istisna'a accounting values based on extracted variables.
    
    Args:
        variables (dict): The extracted variables
        
    Returns:
        dict: Calculated values
    """
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
