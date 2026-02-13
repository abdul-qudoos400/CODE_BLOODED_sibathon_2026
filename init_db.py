"""
Initialize database and load sample data
"""

from models import db, Transaction
from data.sample_data import SAMPLE_TRANSACTIONS
from datetime import datetime, timedelta
import random

def init_database():
    """Initialize database and populate with sample data"""
    
    print("🔄 Initializing database...")
    db.init_db()
    
    print("📝 Loading sample transaction data...")
    session = db.get_session()
    
    try:
        # Generate transactions for the last 90 days
        base_date = datetime.now()
        
        for i, trans_data in enumerate(SAMPLE_TRANSACTIONS):
            # Distribute transactions across last 90 days
            days_ago = random.randint(0, 90)
            transaction_date = base_date - timedelta(days=days_ago)
            
            transaction = Transaction(
                amount=trans_data['amount'],
                category=trans_data['category'],
                description=trans_data['description'],
                merchant=trans_data['merchant'],
                transaction_type='expense',
                date=transaction_date
            )
            session.add(transaction)
        
        session.commit()
        print(f"✓ Successfully loaded {len(SAMPLE_TRANSACTIONS)} sample transactions!")
        
        # Display some stats
        all_trans = session.query(Transaction).all()
        total_spent = sum(t.amount for t in all_trans)
        categories = set(t.category for t in all_trans)
        
        print(f"\n📊 Database Statistics:")
        print(f"   • Total Transactions: {len(all_trans)}")
        print(f"   • Total Spending: ${total_spent:.2f}")
        print(f"   • Categories: {', '.join(sorted(categories))}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error loading data: {e}")
    finally:
        session.close()


def view_transactions():
    """View all transactions"""
    session = db.get_session()
    try:
        transactions = session.query(Transaction).all()
        print(f"\n📋 All Transactions ({len(transactions)} total):")
        print("-" * 80)
        for t in transactions[:10]:  # Show first 10
            print(f"{t.date.strftime('%Y-%m-%d')} | {t.merchant:15} | ${t.amount:8.2f} | {t.category}")
        if len(transactions) > 10:
            print(f"... and {len(transactions) - 10} more transactions")
        print("-" * 80)
    finally:
        session.close()


if __name__ == '__main__':
    init_database()
    view_transactions()
