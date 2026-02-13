"""
Script to load sample transaction data into the database
"""
import pandas as pd
from datetime import datetime
from database import SessionLocal, init_db
from models.transaction import Transaction

def load_sample_data():
    """Load sample transactions from CSV into database"""
    # First, initialize the database
    print("Initializing database...")
    init_db()
    
    # Read CSV file
    df = pd.read_csv('./data/sample_transactions.csv')
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Transaction).delete()
        
        # Add each transaction from CSV
        for index, row in df.iterrows():
            transaction = Transaction(
                amount=float(row['amount']),
                description=str(row['description']),
                merchant=str(row['merchant']) if pd.notna(row['merchant']) else None,
                category=str(row['category']) if pd.notna(row['category']) else None,
                transaction_type=str(row['transaction_type']),
                transaction_date=pd.to_datetime(row['transaction_date']),
                payment_method=str(row['payment_method']) if pd.notna(row['payment_method']) else None,
                notes=str(row['notes']) if pd.notna(row['notes']) else None
            )
            db.add(transaction)
        
        # Commit all changes
        db.commit()
        
        # Verify
        count = db.query(Transaction).count()
        print(f"✓ Successfully loaded {count} transactions!")
        
        # Display sample data
        print("\nSample transactions:")
        transactions = db.query(Transaction).limit(5).all()
        for t in transactions:
            print(f"  - {t.description}: ${t.amount} ({t.category})")
    
    except Exception as e:
        db.rollback()
        print(f"✗ Error loading data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_sample_data()
