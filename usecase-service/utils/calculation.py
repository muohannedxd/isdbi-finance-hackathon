"""
Calculation utilities for the Islamic Finance API.
"""

def calculate_ijarah_values(variables):
    """
    Calculate Ijarah accounting values based on extracted variables.

    Args:
        variables (dict): The extracted variables with keys:
            - purchase_price (float)
            - import_tax (float)
            - freight_charges (float)
            - yearly_rental (float)
            - lease_term (int)
            - residual_value (float)
            - purchase_option (float)

    Returns:
        dict: Calculated values including prime_cost, rou_asset, total_rentals, 
              deferred_cost, terminal_value_diff, amortizable_amount, ijarah_liability
    """
    # Extract and sanitize inputs
    purchase_price = float(variables.get('purchase_price', 0))
    import_tax = float(variables.get('import_tax', 0))
    freight_charges = float(variables.get('freight_charges', 0))
    yearly_rental = float(variables.get('yearly_rental', 0))
    lease_term = int(variables.get('lease_term', 0))
    residual_value = float(variables.get('residual_value', 0))
    purchase_option = float(variables.get('purchase_option', 0))

    # Core calculations
    prime_cost = purchase_price + import_tax + freight_charges
    rou_asset = prime_cost
    total_rentals = yearly_rental * lease_term
    deferred_cost = total_rentals - rou_asset
    terminal_value_diff = residual_value - purchase_option
    amortizable_amount = rou_asset - terminal_value_diff
    ijarah_liability = total_rentals

    return {
        'prime_cost': prime_cost,
        'rou_asset': rou_asset,
        'total_rentals': total_rentals,
        'deferred_cost': deferred_cost,
        'terminal_value_diff': terminal_value_diff,
        'amortizable_amount': amortizable_amount,
        'ijarah_liability': ijarah_liability
    }


def calculate_murabaha_values(variables):
    """
    Calculate Murabaha accounting values based on extracted variables.

    Args:
        variables (dict): The extracted variables with keys:
            - cost_price (float)
            - selling_price (float)
            - profit_rate (float, in %)
            - installments (int)
            - down_payment (float)

    Returns:
        dict: Calculated values including cost_price, selling_price, profit, and installment_amount
    """
    # Extract and sanitize inputs
    cost_price = float(variables.get('cost_price', 0))
    selling_price = float(variables.get('selling_price', 0))
    profit_rate = float(variables.get('profit_rate', 0))
    installments = int(variables.get('installments', 1))
    down_payment = float(variables.get('down_payment', 0))

    results = {
        'cost_price': cost_price,
        'selling_price': selling_price,
        'profit': 0,
        'installment_amount': 0
    }

    if selling_price == 0 and cost_price > 0 and profit_rate > 0:
        selling_price = cost_price * (1 + profit_rate / 100)
        results['selling_price'] = selling_price
    else:
        results['selling_price'] = selling_price

    if selling_price > 0 and cost_price > 0:
        profit = selling_price - cost_price
        results['profit'] = profit

        if installments > 0:
            remaining_amount = selling_price - down_payment
            installment_amount = remaining_amount / installments
            results['installment_amount'] = installment_amount

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
