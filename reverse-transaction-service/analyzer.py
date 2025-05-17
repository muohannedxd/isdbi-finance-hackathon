import os
import re
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
from standards import standards_info, standard_keywords

class IslamicFinanceMultiAgentAnalyzer:
    def __init__(self, api_key):
        """Initialize the multi-agent analyzer with Gemini API key"""
        self.api_key = api_key
        self.configure_genai()
        self.load_standard_data()
        
    def configure_genai(self):
        """Configure the Gemini API"""
        genai.configure(api_key=self.api_key)
        
        # Configure model settings
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "max_output_tokens": 4096,
        }
        
        # Create the model instance
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=self.generation_config
        )
        
    def load_standard_data(self):
        """Load standard data including Arabic terminology"""
        # Standard information (simplified for brevity)
        self.standards_info = standards_info
        
        # Add Arabic terminology for each standard
        self.arabic_terms = {
            "FAS 4": ["مشاركة", "شراكة", "ربح وخسارة"],
            "FAS 7": ["سلم", "سلم موازي", "بيع السلم"],
            "FAS 10": ["استصناع", "استصناع موازي", "عقد الاستصناع"],
            "FAS 28": ["مرابحة", "بيع مؤجل", "بيع بالتقسيط"],
            "FAS 32": ["إجارة", "إجارة منتهية بالتمليك", "تأجير"]
        }
        
        # Standard keywords and patterns (simplified)
        self.standard_keywords = standard_keywords
        
        # Add Arabic keywords to standard_keywords
        for standard, arabic_list in self.arabic_terms.items():
            self.standard_keywords[standard].extend(arabic_list)
            
        # Common ambiguities and clarifications needed
        self.ambiguity_patterns = {
            "hybrid_contracts": [
                "combination", "hybrid", "mixed", "multiple components", 
                "coupled with", "together with", "alongside"
            ],
            "sequential_transactions": [
                "followed by", "subsequent", "then", "after which", 
                "upon completion", "next step"
            ],
            "implicit_structures": [
                "effectively", "in essence", "implicitly", "underlying", 
                "de facto", "in reality", "fundamentally"
            ]
        }
    
    def create_agent_prompts(self, transaction_text, features):
        """Create specialized prompts for each agent"""
        base_context = f"""
        Transaction to analyze:
        {transaction_text}
        
        Feature analysis results:
        - Keywords detected: {features['keywords_by_standard']}
        - Is reversal transaction: {features['is_reversal']}
        - Is impairment-related: {features['is_impairment']}
        - Potential ambiguities: {features['potential_ambiguities']}
        """
        
        # Agent 1: Standards Identifier (Enhanced prompt)
        identifier_prompt = f"""
        {base_context}
        
        You are a lead expert in Islamic Finance standards with 20+ years of experience at AAOIFI. Your task is to precisely identify which AAOIFI Financial Accounting Standards (FAS) are applicable to this transaction.
        
        Step 1: Identify the Islamic contract type(s) in this transaction
        Step 2: Link each component to specific standards
        Step 3: Consider both explicit mentions and implied structures
        Step 4: Weigh standards based on centrality to the transaction
        Step 5: Consider both English and Arabic terminology
        
        Analyze hidden structures: Look for implicit contractual relationships even if not explicitly labeled.
        
        Important contract type guidance:
        - For Istisna'a (FAS 10): Look for manufacturing/construction contracts, progressive payments, 
        customized assets being built to specifications, project financing arrangements, and 
        construction advancements. These may be disguised as general "payments" or "contract revenue".
        - For Ijarah (FAS 32): Focus on rental/lease arrangements with or without transfer of ownership.
        - For Murabaha (FAS 28): Look for cost-plus arrangements with deferred payments.
        - For Musharaka (FAS 4): Focus on partnerships, profit-loss sharing, and joint ventures.
        - For Salam (FAS 7): Identify advance payments for future delivery of standardized goods.
        
        Pay special attention to contract distinctions:
        - Istisna'a vs Ijarah: Istisna'a focuses on asset manufacturing/construction while Ijarah focuses on leasing.
        - Istisna'a vs Salam: Istisna'a is for customized assets, while Salam is for standardized commodities.
        - Look carefully at the substance of transactions involving construction, manufacturing or project financing.
        
        Return your analysis in JSON format:
        {{
            "applicable_standards": [
                {{"standard": "FAS X", "weight": 90, "reason": "specific reason with cited evidence from transaction"}},
                {{"standard": "FAS Y", "weight": 70, "reason": "specific reason with cited evidence"}}
            ],
            "contract_structures": ["primary contract type", "secondary contract type"],
            "potential_hidden_standards": ["FAS Z", "reason for suspecting this standard might apply"]
        }}
        """
        
        # Agent 2: Deep Financial Analyzer (Enhanced prompt)
        financial_prompt = f"""
        {base_context}
        
        You are a senior Islamic accounting specialist with expertise in practical application of AAOIFI standards. Analyze the financial aspects of this transaction with focus on accounting substance over form:
        
        Step 1: Identify all explicit financial entries and their classifications
        Step 2: Determine what accounting principles are being applied
        Step 3: For each entry, identify which specific Islamic contract type it represents
        Step 4: Connect each financial component to specific AAOIFI standards
        Step 5: For complex transactions, determine the primary vs. secondary standards
        
        Journal entry analysis guidance:
        - For progressive payments or staged recognition: Consider FAS 10 (Istisna'a) which allows revenue/profit recognition at stages of completion
        - For construction advances: May indicate Istisna'a financing (FAS 10)
        - For lease/rental payments: Typically indicates Ijarah (FAS 32)
        - For impairment or loss provisions: Look at which underlying contract type is being impaired
        - For reversal entries: Focus on what type of contract the original provision was related to
        
        Be particularly vigilant about:
        - Mixed transactions with elements from multiple standards
        - Indirect references to accounting treatments
        - Construction contract accounting that may indicate Istisna'a
        - Reversal entries that reflect completion of manufacturing or construction contracts
        - Revenue recognition patterns that align with progressive completion
        
        Return your analysis in JSON format:
        {{
            "journal_analysis": "detailed analysis of the entries",
            "primary_standard": "most applicable FAS standard",
            "secondary_standards": ["FAS X", "FAS Y"],
            "confidence": 80,
            "reasoning": "detailed justification with specific references from the transaction",
            "financial_substance": "assessment of substance over form"
        }}
        """
        
        # Agent 3: Arabic Terminology Expert (Enhanced prompt)
        arabic_prompt = f"""
        {base_context}
        
        You are a specialized linguist in Islamic finance with deep expertise in Arabic financial terminology. Your task is to identify any Arabic terms and their implications for AAOIFI standards:
        
        Step 1: Extract all Arabic Islamic finance terminology from the transaction
        Step 2: Analyze the contextual meaning of each term beyond its literal translation
        Step 3: Map these terms to specific AAOIFI standards
        Step 4: Assess regional variations in terminology usage
        Step 5: Identify any semantic ambiguities in the terminology
        
        Pay special attention to:
        - Terms that may have multiple interpretations across different madhahib
        - Regional variations in usage (Gulf vs. Malaysia vs. North Africa)
        - Compound Arabic terms that might indicate hybrid structures
        
        Return your analysis in JSON format:
        {{
            "arabic_terms_detected": ["term1", "term2"],
            "contextual_meanings": {{"term1": "detailed contextual meaning"}},
            "standard_mapping": {{"term1": "FAS X", "term2": "FAS Y"}},
            "primary_standard_based_on_arabic": "most applicable FAS standard",
            "terminological_ambiguities": ["specific ambiguities if any"],
            "confidence": 75
        }}
        """
        
        # Agent 4: Standards Conflict Resolver (Enhanced prompt)
        resolver_prompt = f"""
        {base_context}
        
        You are a senior Shariah scholar specializing in resolving conflicts between Islamic finance standards. When a transaction has elements of multiple standards, your task is to determine which should take precedence:
        
        Step 1: Identify all potentially applicable standards in this transaction
        Step 2: Define the core purpose of the transaction
        Step 3: Apply AAOIFI hierarchy principles for standard conflicts
        Step 4: Consider substance over form principles
        Step 5: Determine which standard best captures the economic reality
        
        Specific contract distinctions:
        - When distinguishing between FAS 10 (Istisna'a) and FAS 32 (Ijarah):
        * FAS 10 applies when the core purpose is manufacturing/constructing an asset to specifications
        * FAS 32 applies when the core purpose is using/leasing an existing asset
        
        - When distinguishing between FAS 10 (Istisna'a) and FAS 28 (Murabaha):
        * FAS 10 applies to customized manufacturing/construction with specifications
        * FAS 28 applies to cost-plus sale of existing assets
        
        - For transactions with loss provisions or reversals:
        * Focus on the underlying contract type, not just the impairment aspect
        
        Specific considerations:
        - For hybrid transactions, analyze which aspect is predominant
        - For sequential transactions, identify the primary objective
        - When multiple interpretations exist, prioritize based on AAOIFI principles
        - For construction or manufacturing arrangements, carefully evaluate if Istisna'a principles apply
        
        Return your analysis in JSON format:
        {{
            "standards_conflicts": [["FAS X", "FAS Y"], ["FAS A", "FAS B"]],
            "conflict_assessment": "analysis of each conflict pair",
            "resolution_reasoning": "detailed explanation with AAOIFI principles applied",
            "primary_standard": "most applicable FAS standard",
            "edge_cases": ["specific edge cases considered"],
            "confidence": 85
        }}
        """
        
        # Agent 5: Ambiguity Detector (New agent)
        ambiguity_prompt = f"""
        {base_context}
        
        You are an Islamic finance expert specialized in detecting ambiguities and hidden structures in financial transactions. Your task is to identify aspects of this transaction that could be interpreted in multiple ways:
        
        Step 1: Analyze the transaction for language that permits multiple interpretations
        Step 2: Identify components that could fall under different standards
        Step 3: Detect potential hidden or implied structures not explicitly stated
        Step 4: Assess whether the transaction might be disguising non-Shariah compliant elements
        Step 5: Determine what additional information would be needed for full clarity
        
        Look specifically for:
        - Vague terminology that could map to multiple contract types
        - Multi-stage transactions where classification might change
        - Missing essential information for proper classification
        - Economic substance that might differ from legal form
        
        Return your analysis in JSON format:
        {{
            "ambiguity_score": 75,
            "ambiguous_elements": [
                {{"element": "specific ambiguous element", "possible_interpretations": ["interpretation1", "interpretation2"]}}
            ],
            "hidden_structures": ["potential hidden contractual relationships"],
            "missing_information": ["specific data points needed for clarity"],
            "clarification_questions": ["specific questions that would resolve ambiguity"]
        }}
        """
        
        # Agent 6: Practical Implementation Expert (New agent)
        implementation_prompt = f"""
        {base_context}
        
        You are a practical implementation expert who has overseen Islamic finance compliance at major financial institutions. Your task is to analyze this transaction from a practical application perspective:
        
        Step 1: Assess how this transaction would be implemented in practice
        Step 2: Identify operational considerations that impact standard application
        Step 3: Consider practical challenges in compliance with theoretical standards
        Step 4: Analyze which standard is most commonly applied in industry practice
        Step 5: Consider regulatory treatment in major Islamic finance jurisdictions
        
        Focus on:
        - Practical execution rather than theoretical classification
        - How similar transactions are typically handled in the industry
        - Jurisdiction-specific considerations (IFSB vs. local frameworks)
        - Implementation challenges that might affect standard selection
        
        Return your analysis in JSON format:
        {{
            "practical_classification": "standard most commonly applied in practice",
            "operational_considerations": ["specific operational factors"],
            "jurisdictional_variations": {{"Malaysia": "standard X", "Bahrain": "standard Y"}},
            "implementation_challenges": ["specific challenges"],
            "industry_precedent": "examples of similar transactions",
            "confidence": 80
        }}
        """
        
        # Agent 7: Shariah Intent Analyst (New agent)
        shariah_prompt = f"""
        {base_context}
        
        You are a Shariah expert specializing in understanding the maqasid (objectives) of Islamic financial transactions. Your task is to analyze the underlying Shariah objectives of this transaction:
        
        Step 1: Identify the core Shariah principles being applied
        Step 2: Assess whether the transaction fulfills genuine Shariah objectives
        Step 3: Determine whether form and substance are aligned from Shariah perspective
        Step 4: Connect Shariah principles to specific AAOIFI standards
        Step 5: Evaluate potential areas of Shariah concern
        
        Focus on:
        - Underlying maqasid al-Shariah in the transaction
        - Potential form-over-substance concerns
        - Whether the transaction achieves genuine risk sharing
        - Assessment of riba, gharar, and maysir avoidance
        
        Return your analysis in JSON format:
        {{
            "shariah_objectives": ["specific objectives identified"],
            "form_vs_substance": "assessment of alignment",
            "shariah_concerns": ["specific concerns if any"],
            "standards_alignment": "which standards best preserve Shariah intent",
            "recommended_standard": "standard that best preserves Shariah objectives",
            "confidence": 85
        }}
        """
        
        clarification_prompt = f"""
        Transaction text:
        {transaction_text}
        
        You are an expert in resolving ambiguities in Islamic finance classifications. This transaction has been analyzed by multiple agents with differing opinions. Your task is to provide definitive clarification:
        
        Identified ambiguities:
        {features.get('potential_ambiguities', [])}
        
        Step 1: Identify the core ambiguities causing disagreement
        Step 2: Analyze which ambiguities could be resolved with available information
        Step 3: Determine which standard would apply if each ambiguity is resolved in different ways
        Step 4: Make a final determination on the most appropriate standard given available information
        Step 5: Specify what information would conclusively resolve remaining ambiguities
        
        Critical contract distinctions to clarify:
        
        - Istisna'a (FAS 10) vs. Ijarah (FAS 32):
        * Istisna'a: Manufacturing or construction of non-existent assets to specification
        * Ijarah: Leasing of existing assets
        * Key question: Is the asset being created/manufactured, or is it already existing?
        
        - Istisna'a (FAS 10) vs. Murabaha (FAS 28):
        * Istisna'a: Custom-made assets according to specifications
        * Murabaha: Purchase and resale of existing assets with markup
        * Key question: Is customization/manufacturing the core aspect, or is it primarily a sale?
        
        - For transactions with reversals or adjustments:
        * Focus on the underlying contract type being reversed, not just the reversal mechanism
        * For loss provision reversals: Evaluate what type of contract was originally impaired
        
        Return your analysis in JSON format:
        {{
            "core_ambiguities": ["specific ambiguities identified"],
            "resolvable_with_available_info": ["which ambiguities can be resolved now"],
            "standard_determination": {{"if interpretation X": "FAS Y", "if interpretation Z": "FAS W"}},
            "most_appropriate_standard": "standard that best fits with available information",
            "confidence": 75,
            "critical_missing_information": ["specific information needed for certainty"],
            "clarification_questions": ["specific questions that would resolve ambiguity"]
        }}
        """
        
        # Return all prompts including the enhanced ones
        return {
            "identifier": identifier_prompt,
            "financial": financial_prompt,
            "arabic": arabic_prompt,  # Assuming this is defined elsewhere in the class
            "resolver": resolver_prompt,
            "ambiguity": ambiguity_prompt,  # Assuming this is defined elsewhere in the class
            "implementation": implementation_prompt,  # Assuming this is defined elsewhere in the class
            "shariah": shariah_prompt,  # Assuming this is defined elsewhere in the class
            "clarification": clarification_prompt
        }
        
    def preprocess_transaction(self, transaction_text):
        """Extract key features from transaction text with enhanced ambiguity detection"""
        text = transaction_text.lower()
        
        # Basic features
        features = {
            "is_reversal": any(term in text for term in ["revers", "adjust", "correct", "terminat", "default", "cancel"]),
            "is_impairment": any(term in text for term in ["impair", "loss", "provision", "allowance"]),
            "keywords_by_standard": {},
            "potential_ambiguities": []
        }
        
        # Count standard-specific keywords
        for standard, keywords in self.standard_keywords.items():
            features["keywords_by_standard"][standard] = sum(1 for keyword in keywords if keyword in text)
            
        # Check for potential ambiguities
        for ambiguity_type, patterns in self.ambiguity_patterns.items():
            if any(pattern in text for pattern in patterns):
                features["potential_ambiguities"].append(ambiguity_type)
                
        # Check for transaction complexity indicators
        complexity_indicators = [
            "complex", "multi-stage", "series of", "arrangement", "structure", 
            "combined", "thereafter", "subsequently"
        ]
        if any(indicator in text for indicator in complexity_indicators):
            features["potential_ambiguities"].append("complex_structure")
            
        return features
    
    def run_agent(self, prompt_type, prompts):
        """Run a single agent analysis"""
        try:
            response = self.model.generate_content(prompts[prompt_type])
            response_text = response.text
            
            # Extract the JSON part
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": f"JSON parsing error for {prompt_type} agent"}
            else:
                return {"error": f"No JSON found in {prompt_type} agent response"}
                
        except Exception as e:
            return {"error": f"API error in {prompt_type} agent: {str(e)}"}
    
    def run_multi_agent_analysis(self, transaction_text):
        """Run concurrent analysis with multiple specialized agents"""
        # Extract features from transaction
        features = self.preprocess_transaction(transaction_text)
        
        # Create agent-specific prompts
        prompts = self.create_agent_prompts(transaction_text, features)
        
        # Run agents in parallel
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                agent_type: executor.submit(self.run_agent, agent_type, prompts)
                for agent_type in prompts.keys()
            }
            
            # Collect results
            agent_results = {
                agent_type: future.result()
                for agent_type, future in futures.items()
            }
        
        # Check for significant ambiguities that need clarification
        clarification_needed = self.check_for_clarification_needs(agent_results, features)
        
        # If clarification is needed, run clarification agent
        if clarification_needed:
            clarified_results = self.run_clarification_agent(transaction_text, agent_results, features)
            # Merge clarification results into agent results
            agent_results["clarification"] = clarified_results
        
        # Combine and prioritize results
        final_result = self.combine_agent_results(agent_results, features)
        
        return final_result
    
    def check_for_clarification_needs(self, agent_results, features):
        """Determine if transaction needs clarification based on agent results"""
        # Check ambiguity agent results
        ambiguity_agent = agent_results.get("ambiguity", {})
        ambiguity_score = ambiguity_agent.get("ambiguity_score", 0)
        
        # Check for disagreement between agents
        standard_votes = {}
        for agent_type in ["identifier", "financial", "arabic", "resolver", "implementation", "shariah"]:
            result = agent_results.get(agent_type, {})
            if "primary_standard" in result:
                std = result["primary_standard"]
                standard_votes[std] = standard_votes.get(std, 0) + 1
            elif "recommended_standard" in result:
                std = result["recommended_standard"]
                standard_votes[std] = standard_votes.get(std, 0) + 1
                
        # Calculate disagreement level
        disagreement_level = 0
        if standard_votes:
            # If there's more than one standard with votes
            if len(standard_votes) > 1:
                top_votes = max(standard_votes.values())
                total_votes = sum(standard_votes.values())
                # Calculate what percentage of votes the top standard got
                consensus_percentage = (top_votes / total_votes) * 100
                # Higher disagreement when consensus is lower
                disagreement_level = 100 - consensus_percentage
        
        # Need clarification if ambiguity is high or agents disagree significantly
        return ambiguity_score > 60 or disagreement_level > 40
    
    def run_clarification_agent(self, transaction_text, agent_results, features):
        """Run a specialized clarification agent to resolve ambiguities"""
        # Extract ambiguities and disagreements to focus on
        ambiguities = agent_results.get("ambiguity", {}).get("ambiguous_elements", [])
        missing_info = agent_results.get("ambiguity", {}).get("missing_information", [])
        
        # Collect different standards proposed by agents
        proposed_standards = {}
        for agent_type, result in agent_results.items():
            if "primary_standard" in result:
                std = result["primary_standard"]
                reason = result.get("reasoning", "")
                proposed_standards[std] = proposed_standards.get(std, []) + [(agent_type, reason)]
            elif "recommended_standard" in result:
                std = result["recommended_standard"]
                reason = result.get("shariah_objectives", "")
                proposed_standards[std] = proposed_standards.get(std, []) + [(agent_type, reason)]
        
        # Create clarification prompt
        clarification_prompt = f"""
        Transaction text:
        {transaction_text}
        
        You are an expert in resolving ambiguities in Islamic finance classifications. This transaction has been analyzed by multiple agents with differing opinions. Your task is to provide definitive clarification:
        
        Identified ambiguities:
        {ambiguities}
        
        Missing information:
        {missing_info}
        
        Proposed standards with reasons:
        {proposed_standards}
        
        Step 1: Identify the core ambiguities causing disagreement
        Step 2: Analyze which ambiguities could be resolved with available information
        Step 3: Determine which standard would apply if each ambiguity is resolved in different ways
        Step 4: Make a final determination on the most appropriate standard given available information
        Step 5: Specify what information would conclusively resolve remaining ambiguities
        
        Critical contract distinctions to clarify:
        
        - For reversals or impairment adjustments:
        * Focus on the UNDERLYING CONTRACT TYPE being reversed, not just the reversal entry
        * Example: A reversal of an impairment on an Istisna'a contract should be classified as FAS 10
        
        - When distinguishing between FAS 10 (Istisna'a) and FAS 32 (Ijarah):
        * The key difference is whether the asset is being CREATED (FAS 10) or USED (FAS 32)
        * Manufacturing, construction, or project financing typically points to Istisna'a (FAS 10)
        
        - Construction contracts or progressively built assets:
        * Even if not explicitly labeled as "Istisna'a", these typically fall under FAS 10
        * Look for payments tied to completion stages, construction advances, or customization
        
        - Profit recognition patterns:
        * Progressive recognition during construction/manufacturing typically indicates Istisna'a (FAS 10)
        * Time-based recognition over a usage period typically indicates Ijarah (FAS 32)
        
        Return your analysis in JSON format:
        {{
            "core_ambiguities": ["specific ambiguities identified"],
            "resolvable_with_available_info": ["which ambiguities can be resolved now"],
            "standard_determination": {{"if interpretation X": "FAS Y", "if interpretation Z": "FAS W"}},
            "most_appropriate_standard": "standard that best fits with available information",
            "confidence": 75,
            "critical_missing_information": ["specific information needed for certainty"],
            "clarification_questions": ["specific questions that would resolve ambiguity"]
        }}
        """
        
        try:
            response = self.model.generate_content(clarification_prompt)
            response_text = response.text
            
            # Extract the JSON part
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return {"error": "JSON parsing error in clarification agent"}
            else:
                return {"error": "No JSON found in clarification agent response"}
                
        except Exception as e:
            return {"error": f"API error in clarification agent: {str(e)}"}
    
    def combine_agent_results(self, agent_results, features):
        """Combine and prioritize results from different agents with confidence weighting"""
        # Extract standards from identifier agent
        applicable_standards = []
        if "applicable_standards" in agent_results.get("identifier", {}):
            applicable_standards = agent_results["identifier"]["applicable_standards"]
        
        # Get primary standard opinions from different agents with weighted voting
        standard_votes = {}
        confidence_values = {}
        reasonings = {}
        
        # Define agent weights
        agent_weights = {
            "identifier": 1.5,
            "financial": 2.0,
            "arabic": 1.0,
            "resolver": 2.0,
            "ambiguity": 0.5,
            "implementation": 1.5,
            "shariah": 1.5,
            "clarification": 2.5
        }
        
        # Adjust weights based on transaction features
        if features["is_reversal"]:
            agent_weights["financial"] += 0.5
        
        if len(features["potential_ambiguities"]) > 0:
            agent_weights["ambiguity"] += 0.5
            agent_weights["resolver"] += 0.5
        
        # Collect votes from each agent
        for agent_type, result in agent_results.items():
            std = None
            confidence = 70  # Default confidence
            reasoning = ""
            
            # Extract standard and confidence based on agent type
            if agent_type == "financial" and "primary_standard" in result:
                std = result["primary_standard"]
                confidence = result.get("confidence", 70)
                reasoning = result.get("reasoning", "")
            elif agent_type == "resolver" and "primary_standard" in result:
                std = result["primary_standard"]
                confidence = result.get("confidence", 70)
                reasoning = result.get("resolution_reasoning", "")
            elif agent_type == "arabic" and "primary_standard_based_on_arabic" in result:
                std = result["primary_standard_based_on_arabic"]
                confidence = result.get("confidence", 70)
                reasoning = "Based on Arabic terminology analysis"
            elif agent_type == "identifier" and "applicable_standards" in result:
                # Consider all standards with their weights from identifier
                for std_info in result["applicable_standards"]:
                    std_name = std_info.get("standard")
                    std_weight = std_info.get("weight", 70)
                    std_reason = std_info.get("reason", "")
                    
                    # Add weighted vote with confidence incorporated
                    if std_name:
                        weight = agent_weights.get(agent_type, 1.0) * (std_weight / 100)
                        standard_votes[std_name] = standard_votes.get(std_name, 0) + weight
                        confidence_values[std_name] = std_weight
                        if std_name not in reasonings:
                            reasonings[std_name] = []
                        reasonings[std_name].append(f"{agent_type}: {std_reason}")
                
                # Skip the standard assignment below since we've already processed all standards
                std = None
            elif agent_type == "implementation" and "practical_classification" in result:
                std = result["practical_classification"]
                confidence = result.get("confidence", 70)
                reasoning = "Based on industry implementation practices"
            elif agent_type == "shariah" and "recommended_standard" in result:
                std = result["recommended_standard"]
                confidence = result.get("confidence", 70)
                reasoning = "Based on Shariah objectives analysis"
            elif agent_type == "clarification" and "most_appropriate_standard" in result:
                std = result["most_appropriate_standard"]
                confidence = result.get("confidence", 70)
                reasoning = "Based on clarification of ambiguities"
            
            # Add weighted vote if a standard was determined
            if std:
                weight = agent_weights.get(agent_type, 1.0) * (confidence / 100)
                standard_votes[std] = standard_votes.get(std, 0) + weight
                confidence_values[std] = confidence_values.get(std, 0) + confidence
                if std not in reasonings:
                    reasonings[std] = []
                reasonings[std].append(f"{agent_type}: {reasoning}")
        
        # Add votes from keyword analysis with confidence adjustment
        for std, count in features["keywords_by_standard"].items():
            if count > 0:
                # Base confidence for keywords starts at 50% and increases with keyword count
                keyword_confidence = min(50 + (count * 5), 75)  
                standard_votes[std] = standard_votes.get(std, 0) + (count * 0.2 * (keyword_confidence / 100))
                confidence_values[std] = confidence_values.get(std, 0) + keyword_confidence
                
        # Calculate average confidence for each standard
        avg_confidence = {}
        for std in confidence_values:
            if std in standard_votes and standard_votes[std] > 0:
                # Normalize by the number of agents that voted for this standard
                vote_count = len([r for r in reasonings.get(std, []) if r])
                avg_confidence[std] = confidence_values[std] / max(vote_count, 1)
            else:
                avg_confidence[std] = 0
        
        # Determine primary standard based on votes weighted by confidence
        primary_standard = "Unknown"
        highest_score = 0
        detailed_justification = ""
        
        for std, votes in standard_votes.items():
            # Apply confidence as a multiplier to the vote weight
            confidence_factor = avg_confidence.get(std, 70) / 100
            weighted_score = votes * confidence_factor
            
            if weighted_score > highest_score:
                highest_score = weighted_score
                primary_standard = std
                detailed_justification = "\n".join(reasonings.get(std, []))
        
        # Build final result
        final_result = {
            "applicable_standards": applicable_standards,
            "primary_standard": primary_standard,
            "detailed_justification": detailed_justification,
            "confidence": min(highest_score * 20, 95),  # Scale to percentage, cap at 95%
            "agent_votes": {std: round(votes, 2) for std, votes in standard_votes.items()},
            "standard_confidence": {std: round(conf, 1) for std, conf in avg_confidence.items()},
            "arabic_analysis": agent_results.get("arabic", {})
        }
        
        # Add ambiguity information
        if "ambiguity" in agent_results:
            final_result["ambiguity_analysis"] = {
                "score": agent_results["ambiguity"].get("ambiguity_score", 0),
                "elements": agent_results["ambiguity"].get("ambiguous_elements", []),
                "missing_information": agent_results["ambiguity"].get("missing_information", [])
            }
        
        # Add clarification information if available
        if "clarification" in agent_results:
            final_result["clarification"] = {
                "core_ambiguities": agent_results["clarification"].get("core_ambiguities", []),
                "critical_missing_information": agent_results["clarification"].get("critical_missing_information", []),
                "clarification_questions": agent_results["clarification"].get("clarification_questions", [])
            }
        
        # Check for consensus level
        total_votes = sum(standard_votes.values())
        top_votes = standard_votes.get(primary_standard, 0)
        consensus_percentage = (top_votes / total_votes * 100) if total_votes > 0 else 0
        final_result["consensus_level"] = round(consensus_percentage, 1)
        
        # Add anomalies
        anomalies = []
        
        # Check for disagreement between agents
        if len(standard_votes) > 1:
            top_standards = sorted(standard_votes.items(), key=lambda x: x[1], reverse=True)
            if len(top_standards) >= 2 and top_standards[0][1] - top_standards[1][1] < 1:
                # Also check confidence difference
                std1, std2 = top_standards[0][0], top_standards[1][0]
                conf1, conf2 = avg_confidence.get(std1, 0), avg_confidence.get(std2, 0)
                if abs(conf1 - conf2) < 15:  # Similar confidence
                    anomalies.append(f"Agent disagreement: Close votes between {std1} and {std2}")
                elif conf2 > conf1:  # Second standard has higher confidence
                    anomalies.append(f"Warning: {std2} has higher confidence ({conf2:.1f}%) than {std1} ({conf1:.1f}%)")
                
        # Check for low confidence
        if final_result["confidence"] < 60:
            anomalies.append(f"Low overall confidence: {final_result['confidence']:.1f}%")
            
        # Check for high ambiguity
        if "ambiguity_analysis" in final_result and final_result["ambiguity_analysis"]["score"] > 70:
            anomalies.append(f"High ambiguity score: {final_result['ambiguity_analysis']['score']}")
            
        # Check for low consensus
        if final_result["consensus_level"] < 50:
            anomalies.append(f"Low consensus level: {final_result['consensus_level']:.1f}%")
        
        # Check for confidence inversion (high votes but low confidence)
        for std, votes in sorted(standard_votes.items(), key=lambda x: x[1], reverse=True)[:3]:
            conf = avg_confidence.get(std, 0)
            if votes > 1.5 and conf < 60:
                anomalies.append(f"Confidence inversion: {std} has strong votes but low confidence ({conf:.1f}%)")
        
        final_result["anomalies"] = anomalies
        
        return final_result
    
    def analyze_transaction(self, transaction_name, transaction_text, expected_standard=None):
        """Analyze a transaction and display results"""
        print(f"Analyzing: {transaction_name}")
        print("-" * 50)
        print(transaction_text[:200] + "..." if len(transaction_text) > 200 else transaction_text)
        print("-" * 50)
        
        # Run multi-agent analysis
        result = self.run_multi_agent_analysis(transaction_text)
        
        # Display results
        print(f"\nPrimary Standard: {result['primary_standard']} (Confidence: {result['confidence']:.1f}%)")
        print(f"Consensus Level: {result['consensus_level']:.1f}%")
        
        # Display agent votes and confidence values together
        print("\nStandard Evaluations:")
        for std in sorted(result["agent_votes"], key=lambda x: result["agent_votes"][x], reverse=True):
            print(f"  • {std}: Votes={result['agent_votes'][std]:.2f}, Confidence={result.get('standard_confidence', {}).get(std, 0):.1f}%")
        
        if result.get("anomalies"):
            print("\n⚠️ Anomalies:")
            for anomaly in result["anomalies"]:
                print(f"  • {anomaly}")
        
        # Show ambiguity analysis if available
        if "ambiguity_analysis" in result:
            print("\nAmbiguity Analysis:")
            print(f"  Score: {result['ambiguity_analysis']['score']}")
            if result['ambiguity_analysis'].get('elements'):
                print("  Ambiguous Elements:")
                for element in result['ambiguity_analysis']['elements'][:3]:  # Show top 3
                    print(f"    • {element}")
        
        # Show clarification information if available
        if "clarification" in result:
            print("\nClarification Needed:")
            if result['clarification'].get('clarification_questions'):
                print("  Recommended Questions:")
                for question in result['clarification']['clarification_questions'][:3]:  # Show top 3
                    print(f"    • {question}")
        
        # Compare with expected standard if provided
        if expected_standard:
            is_correct = result["primary_standard"] == expected_standard
            print(f"\nExpected Standard: {expected_standard}")
            print(f"Correct: {'✓' if is_correct else '✗'}")
        
        print("\n" + "=" * 60 + "\n")
        
        # Create visualizations
        self.visualize_results(transaction_name, result)
        
        return result
    
    def visualize_results(self, transaction_name, result):
        """Create visualizations for the analysis results"""
        # Visualize applicable standards
        if result.get("applicable_standards"):
            plt.figure(figsize=(10, 5))
            standards_df = pd.DataFrame(result["applicable_standards"])
            standards_df = standards_df.sort_values(by="weight", ascending=False)
            
            plt.bar(standards_df["standard"], standards_df["weight"], color="#1f77b4")
            plt.title(f"Applicable Standards for {transaction_name}")
            plt.xlabel("AAOIFI Standards")
            plt.ylabel("Confidence Weight (%)")
            plt.ylim(0, 100)
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout()
            plt.show()
        
        # Visualize agent votes with confidence
        if result.get("agent_votes") and result.get("standard_confidence"):
            plt.figure(figsize=(10, 6))
            standards = list(result["agent_votes"].keys())
            votes = list(result["agent_votes"].values())
            confidences = [result["standard_confidence"].get(std, 0) for std in standards]
            
            # Sort by votes
            sorted_indices = np.argsort(votes)[::-1]
            sorted_standards = [standards[i] for i in sorted_indices]
            sorted_votes = [votes[i] for i in sorted_indices]
            sorted_confidences = [confidences[i] for i in sorted_indices]
            
            # Create figure with two y-axes
            fig, ax1 = plt.subplots(figsize=(10, 5))
            ax2 = ax1.twinx()
            
            # Plot votes on left axis
            bars = ax1.bar(sorted_standards, sorted_votes, color="#ff7f0e", alpha=0.7)
            ax1.set_xlabel("AAOIFI Standards")
            ax1.set_ylabel("Weighted Votes", color="#ff7f0e")
            ax1.tick_params(axis="y", labelcolor="#ff7f0e")
            
            # Plot confidence on right axis
            ax2.plot(sorted_standards, sorted_confidences, "o-", color="#1f77b4", linewidth=2)
            ax2.set_ylabel("Confidence (%)", color="#1f77b4")
            ax2.tick_params(axis="y", labelcolor="#1f77b4")
            ax2.set_ylim(0, 100)
            
            # Highlight the primary standard
            for i, std in enumerate(sorted_standards):
                if std == result["primary_standard"]:
                    bars[i].set_color("#2ca02c")
                    bars[i].set_alpha(1.0)
            
            plt.title(f"Standard Evaluation for {transaction_name}")
            plt.grid(axis="y", linestyle="--", alpha=0.3)
            plt.tight_layout()
            plt.show()