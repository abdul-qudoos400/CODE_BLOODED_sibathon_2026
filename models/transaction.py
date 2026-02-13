"""
Transaction data model and schema
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
from database import Base
from typing import Optional

class Transaction(Base):
    """
    Transaction model for finance tracking app
    Stores all financial transactions
    """
    __tablename__ = "transactions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Transaction Details
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    merchant = Column(String(255), nullable=True)  # Store/vendor name
    category = Column(String(100), nullable=True)  # Will be auto-categorized
    
    # Transaction Type
    transaction_type = Column(String(20), nullable=False)  # 'expense' or 'income'
    
    # Dates
    transaction_date = Column(DateTime, nullable=False)  # When transaction occurred
    created_at = Column(DateTime, server_default=func.now())  # When added to system
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Additional Info
    payment_method = Column(String(50), nullable=True)  # Credit card, cash, bank transfer
    notes = Column(Text, nullable=True)  # User notes
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, category={self.category}, date={self.transaction_date})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "amount": self.amount,
            "description": self.description,
            "merchant": self.merchant,
            "category": self.category,
            "transaction_type": self.transaction_type,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "payment_method": self.payment_method,
            "notes": self.notes
        }


# Define spending categories for the app
EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Education",
    "Fitness",
    "Insurance",
    "Bills & Payments",
    "Personal Care",
    "Groceries",
    "Travel",
    "Other"
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investment",
    "Bonus",
    "Gift",
    "Other Income"
]
