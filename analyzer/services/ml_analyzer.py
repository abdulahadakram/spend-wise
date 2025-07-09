import re
import logging
import decimal
from decimal import Decimal
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLAnalyzer:
    """Machine Learning analyzer for transaction categorization and anomaly detection"""
    
    def __init__(self):
        self.categories = [
            'Food & Dining',
            'Transportation',
            'Shopping',
            'Bills & Utilities',
            'Entertainment',
            'Healthcare',
            'Other'
        ]
        
        # Keywords for each category
        self.category_keywords = {
            'Food & Dining': [
                'restaurant', 'cafe', 'food', 'dining', 'meal', 'lunch', 'dinner',
                'breakfast', 'pizza', 'burger', 'coffee', 'starbucks', 'mcdonalds',
                'kfc', 'subway', 'dominos', 'foodpanda', 'uber eats', 'zomato',
                'bistro', 'porcelain', 'third culture'
            ],
            'Transportation': [
                'uber', 'lyft', 'taxi', 'cab', 'transport', 'fuel', 'gas',
                'petrol', 'diesel', 'parking', 'metro', 'bus', 'train', 'airline',
                'flight', 'car', 'vehicle', 'maintenance', 'repair', 'atm cash'
            ],
            'Shopping': [
                'amazon', 'walmart', 'target', 'shop', 'store', 'mall', 'retail',
                'clothing', 'shoes', 'electronics', 'apparel', 'fashion', 'online',
                'ecommerce', 'purchase', 'buy', 'order', 'pos', 'slack', 'upwork',
                'fiverr', 'instaprint', 'inka', 'paysa', 'maria.b.design', 'royal tag'
            ],
            'Bills & Utilities': [
                'electricity', 'water', 'gas', 'internet', 'phone', 'mobile',
                'utility', 'bill', 'payment', 'service', 'subscription', 'netflix',
                'spotify', 'youtube', 'premium', 'membership', 'charges taxes',
                'bank charges', 'fed', 'telenor', 'batch transfer', 'salary transfer'
            ],
            'Entertainment': [
                'movie', 'cinema', 'theater', 'concert', 'show', 'game', 'gaming',
                'netflix', 'spotify', 'youtube', 'disney', 'hulu', 'amazon prime',
                'entertainment', 'leisure', 'recreation'
            ],
            'Healthcare': [
                'hospital', 'clinic', 'doctor', 'pharmacy', 'medicine', 'medical',
                'health', 'dental', 'vision', 'insurance', 'treatment', 'therapy',
                'prescription', 'drug', 'medicine'
            ]
        }
        
        # Initialize models
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.classifier = LogisticRegression(random_state=42, max_iter=1000)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
        # Train the models with sample data
        self._train_models()
    
    def _train_models(self):
        """Train the ML models with sample data"""
        # Sample training data (in real app, this would come from your bank data)
        sample_descriptions = []
        sample_categories = []
        
        # Generate sample data from keywords
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                sample_descriptions.append(f"Sample transaction with {keyword}")
                sample_categories.append(category)
        
        # Add some "Other" category samples
        other_samples = [
            "ATM withdrawal", "Bank transfer", "Deposit", "Interest payment",
            "Service charge", "Fee", "Unknown transaction"
        ]
        for sample in other_samples:
            sample_descriptions.append(sample)
            sample_categories.append('Other')
        
        # Train the classifier
        if sample_descriptions:
            X = self.vectorizer.fit_transform(sample_descriptions)
            self.classifier.fit(X, sample_categories)
    
    def analyze_transactions(self, transactions) -> Dict[str, Any]:
        """Analyze transactions and return insights"""
        logger.info(f"Analyzing {len(transactions)} transactions")
        
        if not transactions:
            return self._empty_analysis()
        
        # Convert to list if it's a QuerySet
        if hasattr(transactions, 'values'):
            transactions = list(transactions.values())
        
        # Calculate basic statistics with error handling
        total_income = 0.0
        total_expenses = 0.0
        
        for t in transactions:
            try:
                amount = float(t['amount']) if t['amount'] is not None else 0.0
                if t['type'] == 'CREDIT':
                    total_income += amount
                elif t['type'] == 'DEBIT':
                    total_expenses += amount
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                logger.warning(f"Error converting amount for transaction {t.get('description', 'Unknown')}: {e}")
                continue
        
        net_amount = total_income - total_expenses
        
        logger.info(f"Total income: {total_income}, expenses: {total_expenses}, net: {net_amount}")
        
        # Categorize transactions
        categorized_transactions = self._categorize_transactions(transactions)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(transactions)
        logger.info(f"Found {len(anomalies)} anomalies")
        
        # Generate insights
        insights = self._generate_insights(transactions, total_income, total_expenses)
        
        result = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_amount': net_amount,
            'category_breakdown': categorized_transactions,
            'anomalies': anomalies,
            'insights': insights
        }
        
        return result
    
    def _categorize_transactions(self, transactions: List[Dict]) -> Dict[str, float]:
        """Categorize transactions and return breakdown"""
        category_totals = {cat: 0.0 for cat in self.categories}
        
        credit_count = 0
        debit_count = 0
        
        for transaction in transactions:
            logger.info(f"Processing transaction: {transaction['description'][:50]}... Type: {transaction['type']}, Amount: {transaction['amount']}")
            
            if transaction['type'] == 'DEBIT':  # Only categorize expenses
                debit_count += 1
                description = transaction['description'].lower()
                
                # Use ML classifier
                category = self._classify_transaction(description)
                try:
                    amount = float(transaction['amount']) if transaction['amount'] is not None else 0.0
                    category_totals[category] += amount
                    logger.info(f"Categorized as {category}: {amount}")
                except (ValueError, TypeError, decimal.InvalidOperation) as e:
                    logger.warning(f"Error converting amount for categorization: {e}")
                    continue
            elif transaction['type'] == 'CREDIT':
                credit_count += 1
        
        logger.info(f"Total CREDIT transactions: {credit_count}, DEBIT transactions: {debit_count}")
        return category_totals
    
    def _classify_transaction(self, description: str) -> str:
        """Classify a transaction using ML"""
        try:
            # Vectorize the description
            X = self.vectorizer.transform([description])
            
            # Predict category
            prediction = self.classifier.predict(X)[0]
            return prediction
        except Exception as e:
            # Fallback to keyword matching
            return self._keyword_classify(description)
    
    def _keyword_classify(self, description: str) -> str:
        """Fallback classification using keywords"""
        description_lower = description.lower()
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return category
        
        return 'Other'
    
    def _detect_anomalies(self, transactions: List[Dict]) -> List[Dict]:
        """Detect anomalous transactions"""
        if len(transactions) < 3:
            return []
        
        # Prepare features for anomaly detection with error handling
        amounts = []
        for t in transactions:
            try:
                amount = float(t['amount']) if t['amount'] is not None else 0.0
                amounts.append(amount)
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                logger.warning(f"Error converting amount for anomaly detection: {e}")
                amounts.append(0.0)  # Use 0 as fallback
        
        amounts_2d = np.array(amounts).reshape(-1, 1)
        
        # Scale the amounts
        amounts_scaled = self.scaler.fit_transform(amounts_2d)
        
        # Detect anomalies
        anomaly_labels = self.anomaly_detector.fit_predict(amounts_scaled)
        
        # Return anomalous transactions
        anomalies = []
        for i, (transaction, is_anomaly) in enumerate(zip(transactions, anomaly_labels)):
            if is_anomaly == -1:  # -1 indicates anomaly
                try:
                    amount = float(transaction['amount']) if transaction['amount'] is not None else 0.0
                    anomaly_data = {
                        'date': transaction['date'].isoformat() if hasattr(transaction['date'], 'isoformat') else str(transaction['date']),
                        'description': transaction['description'],
                        'amount': amount,
                        'type': transaction['type'],
                        'reason': 'Unusual amount compared to other transactions'
                    }
                    anomalies.append(anomaly_data)
                except (ValueError, TypeError, decimal.InvalidOperation) as e:
                    logger.warning(f"Error converting amount for anomaly: {e}")
                    continue
        
        return anomalies
    
    def _generate_insights(self, transactions: List[Dict], total_income: float, total_expenses: float) -> Dict[str, Any]:
        """Generate insights from transaction data"""
        insights = {}
        
        # Spending vs Income ratio
        if total_income > 0:
            spending_ratio = (total_expenses / total_income) * 100
            insights['spending_ratio'] = round(spending_ratio, 2)
            
            if spending_ratio > 90:
                insights['spending_warning'] = "Your spending is very high relative to income"
            elif spending_ratio > 70:
                insights['spending_warning'] = "Consider reducing expenses to save more"
            else:
                insights['spending_warning'] = "Good spending control!"
        
        # Most common spending category
        if transactions:
            debit_transactions = [t for t in transactions if t['type'] == 'DEBIT']
            if debit_transactions:
                categories = [self._classify_transaction(t['description'].lower()) for t in debit_transactions]
                if categories:
                    most_common = max(set(categories), key=categories.count)
                    insights['top_category'] = most_common
        
        # Transaction frequency
        insights['total_transactions'] = len(transactions)
        
        # Calculate average transaction amount with error handling
        total_amount = 0.0
        valid_transactions = 0
        for t in transactions:
            try:
                amount = float(t['amount']) if t['amount'] is not None else 0.0
                total_amount += amount
                valid_transactions += 1
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                logger.warning(f"Error converting amount for average calculation: {e}")
                continue
        
        insights['avg_transaction_amount'] = round(total_amount / valid_transactions, 2) if valid_transactions > 0 else 0.0
        
        return insights
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'total_income': 0.0,
            'total_expenses': 0.0,
            'net_amount': 0.0,
            'category_breakdown': {cat: 0.0 for cat in self.categories},
            'anomalies': [],
            'insights': {}
        } 