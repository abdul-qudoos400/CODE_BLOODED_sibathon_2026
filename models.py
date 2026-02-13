"""
Database Models for Finance Tracking App
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Transaction(Base):
    """Transaction Model"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)  # Food, Transport, Utilities, etc.
    date = Column(DateTime, default=datetime.now, nullable=False)
    description = Column(String(255), nullable=False)
    merchant = Column(String(100))
    transaction_type = Column(String(10), default='expense')  # 'expense' or 'income'
    user_id = Column(Integer, default=1)  # For future multi-user support
    is_recurring = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, category={self.category}, description={self.description})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'date': self.date.isoformat(),
            'description': self.description,
            'merchant': self.merchant,
            'transaction_type': self.transaction_type,
            'is_recurring': self.is_recurring
        }


class Budget(Base):
    """Budget Model"""
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(50), nullable=False, unique=True)
    limit_amount = Column(Float, nullable=False)
    spent_amount = Column(Float, default=0.0)
    month = Column(String(7))  # YYYY-MM format
    user_id = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<Budget(category={self.category}, limit={self.limit_amount}, spent={self.spent_amount})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'limit_amount': self.limit_amount,
            'spent_amount': self.spent_amount,
            'month': self.month,
            'remaining': self.limit_amount - self.spent_amount
        }


class SpendingInsight(Base):
    """AI-Generated Insights"""
    __tablename__ = 'spending_insights'
    
    id = Column(Integer, primary_key=True)
    insight_text = Column(String(500), nullable=False)
    category = Column(String(50))
    date_generated = Column(DateTime, default=datetime.now)
    insight_type = Column(String(50))  # 'trend', 'alert', 'anomaly', 'recommendation'
    user_id = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<SpendingInsight(type={self.insight_type}, text={self.insight_text})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'insight_text': self.insight_text,
            'category': self.category,
            'insight_type': self.insight_type,
            'date_generated': self.date_generated.isoformat()
        }


class Database:
    """Database Connection Manager"""
    
    def __init__(self, db_url='sqlite:///finance_tracker.db'):
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print("✓ Database initialized successfully!")
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def add_transaction(self, amount, category, description, merchant=None, transaction_type='expense'):
        """Add a new transaction"""
        session = self.get_session()
        try:
            transaction = Transaction(
                amount=amount,
                category=category,
                description=description,
                merchant=merchant,
                transaction_type=transaction_type
            )
            session.add(transaction)
            session.commit()
            return transaction
        except Exception as e:
            session.rollback()
            print(f"Error adding transaction: {e}")
        finally:
            session.close()
    
    def get_all_transactions(self):
        """Get all transactions"""
        session = self.get_session()
        try:
            return session.query(Transaction).all()
        finally:
            session.close()
    
    def get_transactions_by_category(self, category):
        """Get transactions by category"""
        session = self.get_session()
        try:
            return session.query(Transaction).filter_by(category=category).all()
        finally:
            session.close()
    
    def get_monthly_spending(self, month):
        """Get spending for a specific month (format: YYYY-MM)"""
        session = self.get_session()
        try:
            return session.query(Transaction).filter(
                Transaction.date.startswith(month)
            ).all()
        finally:
            session.close()


# Initialize database connection
db = Database()

if __name__ == '__main__':
    db.init_db()
