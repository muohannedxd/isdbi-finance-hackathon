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
        variables (dict): The extracted variables including:
            - contract_value: Value of the client contract
            - total_cost: Cost paid to the contractor
            - upfront_payment: Upfront payment to contractor (if applicable)
            - completion_payment: Payment at completion to contractor (if applicable)
            - delivery_period: Total delivery period in months
            - installments: Number of payment installments
            - payment_terms: Description of payment terms
            
    Returns:
        dict: Calculated values including quarterly progress metrics
    """
    results = {}
    
    # Extract base values
    contract_value = float(variables.get('contract_value', 0))
    total_cost = float(variables.get('total_cost', 0))
    delivery_period = int(variables.get('delivery_period', 12))  # Default to 12 months
    installments = int(variables.get('installments', 4))  # Default to 4 installments
    
    # Handle special payment structure if provided
    upfront_payment = float(variables.get('upfront_payment', 0))
    completion_payment = float(variables.get('completion_payment', 0))
    
    # Calculate expected profit
    expected_profit = contract_value - total_cost
    profit_margin = (expected_profit / contract_value) * 100 if contract_value > 0 else 0
    
    results['contract_value'] = contract_value
    results['total_cost'] = total_cost
    results['expected_profit'] = expected_profit
    results['profit_margin'] = profit_margin
    
    # Calculate quarterly progress
    quarterly_results = []
    
    # Determine if we have a custom cost schedule or should use even distribution
    has_custom_cost_schedule = upfront_payment > 0 or completion_payment > 0
    
    # Special case for parallel Istisna'a with upfront and completion payments
    if has_custom_cost_schedule:
        # Calculate the remaining cost to be distributed across quarters (excluding upfront & completion)
        distributed_cost = total_cost - (upfront_payment + completion_payment)
        quarterly_distributed_cost = distributed_cost / 4 if distributed_cost > 0 else 0
        
        # Track previous revenue and profit for incremental calculations
        prev_revenue = 0
        prev_profit = 0
        
        for i in range(1, 5):
            percentage = i * 25  # Q1=25%, Q2=50%, Q3=75%, Q4=100%
            
            # For Q1, include upfront payment
            if i == 1:
                quarterly_cost = upfront_payment + quarterly_distributed_cost
            # For Q4, include completion payment
            elif i == 4:
                quarterly_cost = completion_payment + quarterly_distributed_cost
            # For middle quarters, just the distributed cost
            else:
                quarterly_cost = quarterly_distributed_cost
            
            # Calculate cumulative cost through this quarter
            cumulative_cost = upfront_payment + (quarterly_distributed_cost * i)
            if i == 4:  # Add completion payment in last quarter
                cumulative_cost += completion_payment
            
            # Calculate revenue and profit based on percentage of completion
            quarterly_revenue = contract_value * (percentage / 100)
            quarterly_profit = expected_profit * (percentage / 100)
            
            # Calculate incremental values (what's recognized in this quarter)
            incremental_revenue = quarterly_revenue - prev_revenue
            incremental_profit = quarterly_profit - prev_profit
            
            # Update previous values for next iteration
            prev_revenue = quarterly_revenue
            prev_profit = quarterly_profit
            
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
    else:
        # Standard even distribution across quarters
        prev_revenue = 0
        prev_profit = 0
        
        for i in range(1, 5):
            percentage = i * 25  # Q1=25%, Q2=50%, Q3=75%, Q4=100%
            
            # Calculate costs
            quarterly_cost = total_cost / 4  # Cost per quarter
            cumulative_cost = quarterly_cost * i  # Cumulative cost through this quarter
            
            # Calculate revenue and profit based on percentage of completion
            quarterly_revenue = contract_value * (percentage / 100)
            quarterly_profit = expected_profit * (percentage / 100)
            
            # Calculate incremental values (what's recognized this quarter)
            incremental_revenue = quarterly_revenue - prev_revenue
            incremental_profit = quarterly_profit - prev_profit
            
            # Update previous values for next iteration
            prev_revenue = quarterly_revenue
            prev_profit = quarterly_profit
            
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
