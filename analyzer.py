"""
Transaction Categorizer and Analysis Module
Phase 1: Core Data Analysis
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import json
from datetime import datetime

class TransactionAnalyzer:
    """Analyze and categorize transactions"""
    
    def __init__(self):
        self.categorizer = None
        self.category_stats = {}
        self.spending_trends = {}
        
    def train_categorizer(self, training_data):
        """
        Train a machine learning model to categorize transactions
        
        training_data: list of tuples [(description, category), ...]
        """
        descriptions = [item[0] for item in training_data]
        categories = [item[1] for item in training_data]
        
        # Create a pipeline with TF-IDF vectorizer and Naive Bayes classifier
        self.categorizer = Pipeline([
            ('tfidf', TfidfVectorizer(lowercase=True, stop_words='english')),
            ('clf', MultinomialNB())
        ])
        
        # Train the model
        self.categorizer.fit(descriptions, categories)
        print(f"✓ Model trained on {len(training_data)} examples")
        return True
    
    def predict_category(self, description):
        """Predict category for a transaction description"""
        if self.categorizer is None:
            return None
        
        prediction = self.categorizer.predict([description])[0]
        confidence = self.categorizer.predict_proba([description]).max()
        
        return {
            'predicted_category': prediction,
            'confidence': round(confidence, 3)
        }
    
    def analyze_spending_patterns(self, transactions_df):
        """Analyze spending patterns from transactions"""
        
        if len(transactions_df) == 0:
            return {}
        
        analysis = {}
        
        # Total spending by category
        category_totals = transactions_df.groupby('category')['amount'].sum().to_dict()
        analysis['total_by_category'] = {k: round(v, 2) for k, v in category_totals.items()}
        
        # Average transaction by category
        category_avg = transactions_df.groupby('category')['amount'].mean().to_dict()
        analysis['average_by_category'] = {k: round(v, 2) for k, v in category_avg.items()}
        
        # Count by category
        category_count = transactions_df.groupby('category').size().to_dict()
        analysis['count_by_category'] = category_count
        
        # Total spending
        analysis['total_spending'] = round(transactions_df['amount'].sum(), 2)
        
        # Highest spending category
        if category_totals:
            highest_category = max(category_totals, key=category_totals.get)
            analysis['highest_spending_category'] = {
                'category': highest_category,
                'amount': round(category_totals[highest_category], 2)
            }
        
        # Average transaction
        analysis['average_transaction'] = round(transactions_df['amount'].mean(), 2)
        
        return analysis
    
    def detect_anomalies(self, transactions_df, threshold=2.0):
        """Detect unusual transactions (anomalies)"""
        
        anomalies = []
        
        for category in transactions_df['category'].unique():
            category_trans = transactions_df[transactions_df['category'] == category]
            
            if len(category_trans) < 2:
                continue
            
            mean = category_trans['amount'].mean()
            std = category_trans['amount'].std()
            
            # Find transactions beyond threshold standard deviations
            for idx, row in category_trans.iterrows():
                z_score = abs((row['amount'] - mean) / std) if std > 0 else 0
                
                if z_score > threshold:
                    anomalies.append({
                        'description': row['description'],
                        'category': row['category'],
                        'amount': round(row['amount'], 2),
                        'z_score': round(z_score, 2),
                        'anomaly_type': 'unusually_high' if row['amount'] > mean else 'unusually_low'
                    })
        
        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)
    
    def generate_insights(self, transactions_df):
        """Generate AI insights from spending data"""
        
        insights = []
        analysis = self.analyze_spending_patterns(transactions_df)
        
        if not analysis:
            return insights
        
        # Insight 1: Total spending
        total = analysis['total_spending']
        insights.append({
            'type': 'summary',
            'text': f"Total spending analyzed: ${total}",
            'priority': 'info'
        })
        
        # Insight 2: Highest spending category
        if 'highest_spending_category' in analysis:
            highest = analysis['highest_spending_category']
            percentage = (highest['amount'] / total * 100) if total > 0 else 0
            insights.append({
                'type': 'trend',
                'text': f"{highest['category']} is your highest spending category at ${highest['amount']} ({percentage:.1f}%)",
                'priority': 'warning' if percentage > 40 else 'info'
            })
        
        # Insight 3: Average transaction
        avg = analysis['average_transaction']
        insights.append({
            'type': 'trend',
            'text': f"Average transaction amount: ${avg}",
            'priority': 'info'
        })
        
        # Insight 4: Most frequent category
        count_by_cat = analysis['count_by_category']
        if count_by_cat:
            most_frequent = max(count_by_cat, key=count_by_cat.get)
            insights.append({
                'type': 'trend',
                'text': f"Most frequent category: {most_frequent} ({count_by_cat[most_frequent]} transactions)",
                'priority': 'info'
            })
        
        return insights
    
    def get_recommendations(self, transactions_df):
        """Generate budget recommendations"""
        
        recommendations = []
        analysis = self.analyze_spending_patterns(transactions_df)
        
        if not analysis or 'total_by_category' not in analysis:
            return recommendations
        
        category_totals = analysis['total_by_category']
        total_spending = analysis['total_spending']
        
        # Recommend 30% of spending for top category as budget
        if category_totals:
            for category, amount in category_totals.items():
                percentage = (amount / total_spending * 100) if total_spending > 0 else 0
                
                # If a category is more than 40% of spending, flag it
                if percentage > 40:
                    recommendations.append({
                        'category': category,
                        'message': f"Consider reducing {category} spending (currently {percentage:.1f}%)",
                        'suggested_budget': round(amount * 0.8, 2),  # 20% reduction
                        'priority': 'high'
                    })
                else:
                    recommendations.append({
                        'category': category,
                        'message': f"Budget recommendation for {category}",
                        'suggested_budget': round(amount * 1.1, 2),  # 10% buffer
                        'priority': 'low'
                    })
        
        return recommendations


class MockTransactionDB:
    """Mock database for testing (will be replaced with actual DB)"""
    
    def __init__(self, transactions):
        self.transactions = transactions
    
    def get_dataframe(self):
        """Convert transactions to pandas DataFrame"""
        df = pd.DataFrame(self.transactions)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df


def main():
    """Test the transaction analyzer"""
    
    from data.sample_data import SAMPLE_TRANSACTIONS, TRAINING_DATA
    
    print("=" * 80)
    print("PHASE 1: TRANSACTION DATA MODEL & ANALYSIS")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = TransactionAnalyzer()
    
    # Train categorizer
    print("\n1️⃣  TRAINING CATEGORIZATION MODEL")
    print("-" * 80)
    analyzer.train_categorizer(TRAINING_DATA)
    
    # Test predictions
    print("\n2️⃣  TESTING CATEGORIZATION")
    print("-" * 80)
    test_descriptions = [
        "Lunch at restaurant",
        "Gas fill-up Shell",
        "Netflix subscription",
        "Grocery shopping Walmart"
    ]
    
    for desc in test_descriptions:
        result = analyzer.predict_category(desc)
        print(f"'{desc}' -> {result['predicted_category']} (confidence: {result['confidence']})")
    
    # Analyze spending patterns
    print("\n3️⃣  ANALYZING SPENDING PATTERNS")
    print("-" * 80)
    db = MockTransactionDB(SAMPLE_TRANSACTIONS)
    df = db.get_dataframe()
    
    analysis = analyzer.analyze_spending_patterns(df)
    print(f"Total Spending: ${analysis['total_spending']}")
    print(f"Average Transaction: ${analysis['average_transaction']}")
    print(f"\nSpending by Category:")
    for cat, amount in sorted(analysis['total_by_category'].items(), key=lambda x: x[1], reverse=True):
        count = analysis['count_by_category'][cat]
        print(f"  {cat:15} ${amount:8.2f}  ({count} transactions)")
    
    # Detect anomalies
    print("\n4️⃣  DETECTING ANOMALIES")
    print("-" * 80)
    anomalies = analyzer.detect_anomalies(df)
    if anomalies:
        print(f"Found {len(anomalies)} anomalies:")
        for anom in anomalies[:5]:
            print(f"  • {anom['description']}: ${anom['amount']} (z-score: {anom['z_score']})")
    else:
        print("No significant anomalies detected")
    
    # Generate insights
    print("\n5️⃣  AI-GENERATED INSIGHTS")
    print("-" * 80)
    insights = analyzer.generate_insights(df)
    for insight in insights:
        print(f"  ℹ️  [{insight['type']}] {insight['text']}")
    
    # Get recommendations
    print("\n6️⃣  BUDGET RECOMMENDATIONS")
    print("-" * 80)
    recommendations = analyzer.get_recommendations(df)
    for rec in recommendations[:5]:
        print(f"  💡 {rec['category']}: Suggested budget = ${rec['suggested_budget']}")
        print(f"     {rec['message']}")
    
    print("\n" + "=" * 80)
    print("✓ PHASE 1 COMPLETE: Data models and analysis ready!")
    print("=" * 80)


if __name__ == '__main__':
    main()
