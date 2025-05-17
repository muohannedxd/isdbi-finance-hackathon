"""
Constants used throughout the Islamic Finance API.
"""

# API and model configuration
API_METHOD = "gemini"  # Options: "gemini" or "together"
CHROMA_PATH = "chroma"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
TOGETHER_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_LLM_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free" if API_METHOD == "together" else GEMINI_MODEL

# Standard types
STANDARD_TYPE_MURABAHA = "MURABAHA"
STANDARD_TYPE_SALAM = "SALAM"
STANDARD_TYPE_ISTISNA = "ISTISNA"
STANDARD_TYPE_IJARAH = "IJARAH"
STANDARD_TYPE_SUKUK = "SUKUK"

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

# Prompt templates
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

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
[List all monetary values, contract terms, payment structures, and financial variables derived from the scenario]

CALCULATIONS
------------------------------
Step 1: Contract Value and Profit Determination
  - Total Contract Value = [amount]
  - Total Estimated Cost = [amount]
  - Expected Profit = Contract Value - Total Cost = [calculation]
  - Profit Margin = (Expected Profit / Contract Value) × 100 = [calculation]

Step 2: Payment Terms and Timeline
  - Delivery Period: [e.g., 12 months or 4 quarters]
  - Payment Schedule: [Describe structure – e.g., Upfront %, Monthly, On Completion, etc.]
  - Parallel Istisna'a: [Yes/No – explain if applicable]

Step 3: Periodic Progress and Recognition

  Period | Cumulative Cost | % Completion | Revenue | Profit | Incremental Revenue | Incremental Profit
  -------|------------------|--------------|---------|--------|----------------------|---------------------
  [List all periods with values calculated]

[For each period:]
- Cumulative Cost = [how derived]
- Percentage Completion = Cumulative Cost / Total Cost = [calculation]
- Revenue = Contract Value × % Completion = [calculation]
- Incremental Revenue = Current Revenue - Prior Revenue = [calculation]
- Profit = Expected Profit × % Completion = [calculation]
- Incremental Profit = Current Profit - Prior Profit = [calculation]

JOURNAL ENTRIES
------------------------------
[Show entries for each period using this format:]

Period [X] - [X]% Completion:

Dr. Work-in-Progress – Istisna'a     [amount]
    Cr. Bank / Payables              [amount]

Dr. Istisna'a Receivable             [amount]
    Cr. Istisna'a Revenue            [amount]

Dr. Istisna'a Cost of Sales          [amount]
    Cr. Work-in-Progress             [amount]

[Also include any client or contractor payments made during this period]

EXPLANATION
------------------------------
[Detailed explanation covering:]

1. How the contract satisfies Istisna'a principles
2. Why revenue/profit is recognized over time under FAS 10
3. How the specific payment structure affects accounting entries
4. Parallel Istisna'a implications (if any)
5. References to relevant AAOIFI clauses
6. Any assumptions or special considerations applied

SUMMARY LEDGER
------------------------------
[Summarized ledger balances:]

Work-in-Progress – Istisna'a:
  Opening Balance: [ ]
  Dr: [ ]
  Cr: [ ]
  Closing Balance: [ ]

Istisna'a Receivable:
  Opening Balance: [ ]
  Dr: [ ]
  Cr: [ ]
  Closing Balance: [ ]

Istisna'a Revenue:
  Opening Balance: [ ]
  Cr: [ ]
  Closing Balance: [ ]

Istisna'a Cost of Sales:
  Opening Balance: [ ]
  Dr: [ ]
  Closing Balance: [ ]
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
  Purchase Price = [Show exact amount from scenario]
  Import Tax = [Show exact amount from scenario]
  Freight Charges = [Show exact amount from scenario]
  Prime Cost = Purchase Price + Import Tax + Freight Charges = [Show calculation with actual numbers]
  Purchase Option Price = [Show exact amount from scenario]
  ROU Asset = Prime Cost = [Show final calculated amount]

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

def get_prompt_for_standard(standard_type, include_examples=True):
    """
    Get the appropriate prompt template for the detected standard.
    
    Args:
        standard_type (str): The standard type to get prompt for
        include_examples (bool): Whether to include validated examples in the prompt
        
    Returns:
        str: The prompt template for the standard
    """
    prompt_template = ""
    
    if standard_type == STANDARD_TYPE_MURABAHA:
        prompt_template = MURABAHA_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_SALAM:
        prompt_template = SALAM_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_ISTISNA:
        prompt_template = ISTISNA_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_IJARAH:
        prompt_template = IJARAH_PROMPT_TEMPLATE
    elif standard_type == STANDARD_TYPE_SUKUK:
        prompt_template = SUKUK_PROMPT_TEMPLATE
    else:
        return PROMPT_TEMPLATE

    # If examples should be included, add them to the prompt
    if include_examples:
        # Import here to avoid circular import
        from utils.examples import get_examples_as_few_shot
        examples = get_examples_as_few_shot(standard_type)
        if examples:
            # Insert examples before the SCENARIO section
            scenario_marker = "SCENARIO:"
            if scenario_marker in prompt_template:
                parts = prompt_template.split(scenario_marker)
                prompt_template = f"{parts[0]}\nVALIDATED EXAMPLES:\n{examples}\n\n{scenario_marker}{parts[1]}"
    
    return prompt_template
