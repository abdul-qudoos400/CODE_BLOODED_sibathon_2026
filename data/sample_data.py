"""
Sample transaction data for training and testing
"""

SAMPLE_TRANSACTIONS = [
    # Food & Dining
    {'amount': 45.50, 'category': 'Food', 'description': 'Lunch at restaurant', 'merchant': 'Pizza Hut'},
    {'amount': 12.99, 'category': 'Food', 'description': 'Coffee and snacks', 'merchant': 'Starbucks'},
    {'amount': 78.50, 'category': 'Food', 'description': 'Grocery shopping', 'merchant': 'Walmart'},
    {'amount': 35.00, 'category': 'Food', 'description': 'Dinner with family', 'merchant': 'Olive Garden'},
    {'amount': 8.50, 'category': 'Food', 'description': 'Fast food breakfast', 'merchant': 'McDonalds'},
    
    # Transportation
    {'amount': 50.00, 'category': 'Transport', 'description': 'Gas fill-up', 'merchant': 'Shell'},
    {'amount': 25.00, 'category': 'Transport', 'description': 'Uber ride to office', 'merchant': 'Uber'},
    {'amount': 5.50, 'category': 'Transport', 'description': 'Bus fare', 'merchant': 'Metro'},
    {'amount': 120.00, 'category': 'Transport', 'description': 'Car maintenance', 'merchant': 'AutoWorks'},
    {'amount': 15.00, 'category': 'Transport', 'description': 'Parking fee', 'merchant': 'Parking Garage'},
    
    # Utilities
    {'amount': 89.99, 'category': 'Utilities', 'description': 'Electricity bill', 'merchant': 'Electric Co'},
    {'amount': 45.00, 'category': 'Utilities', 'description': 'Internet bill', 'merchant': 'Comcast'},
    {'amount': 60.00, 'category': 'Utilities', 'description': 'Water bill', 'merchant': 'Water Dept'},
    {'amount': 35.50, 'category': 'Utilities', 'description': 'Mobile phone bill', 'merchant': 'Verizon'},
    
    # Entertainment
    {'amount': 14.99, 'category': 'Entertainment', 'description': 'Movie ticket', 'merchant': 'AMC Theaters'},
    {'amount': 9.99, 'category': 'Entertainment', 'description': 'Streaming subscription', 'merchant': 'Netflix'},
    {'amount': 50.00, 'category': 'Entertainment', 'description': 'Concert tickets', 'merchant': 'Ticketmaster'},
    {'amount': 25.00, 'category': 'Entertainment', 'description': 'Gaming purchase', 'merchant': 'Steam'},
    
    # Shopping
    {'amount': 120.00, 'category': 'Shopping', 'description': 'Clothing purchase', 'merchant': 'H&M'},
    {'amount': 85.00, 'category': 'Shopping', 'description': 'Electronics', 'merchant': 'Best Buy'},
    {'amount': 45.00, 'category': 'Shopping', 'description': 'Shoes', 'merchant': 'Nike Store'},
    {'amount': 95.00, 'category': 'Shopping', 'description': 'Book purchase', 'merchant': 'Amazon'},
    
    # Health & Fitness
    {'amount': 50.00, 'category': 'Health', 'description': 'Gym membership', 'merchant': 'Gold Gym'},
    {'amount': 30.00, 'category': 'Health', 'description': 'Doctor visit', 'merchant': 'Clinic'},
    {'amount': 25.00, 'category': 'Health', 'description': 'Medicine', 'merchant': 'Pharmacy'},
    {'amount': 15.00, 'category': 'Health', 'description': 'Yoga class', 'merchant': 'Yoga Studio'},
    
    # Miscellaneous
    {'amount': 200.00, 'category': 'Other', 'description': 'Rent payment', 'merchant': 'Landlord'},
    {'amount': 40.00, 'category': 'Other', 'description': 'Gift purchase', 'merchant': 'Target'},
    {'amount': 60.00, 'category': 'Other', 'description': 'Home supplies', 'merchant': 'Home Depot'},
]

# Training data for categorization model
TRAINING_DATA = [
    ('Pizza Hut lunch', 'Food'),
    ('Coffee at Starbucks', 'Food'),
    ('Grocery shopping at Walmart', 'Food'),
    ('Dinner at restaurant', 'Food'),
    ('Fast food breakfast', 'Food'),
    ('Gas station fill-up', 'Transport'),
    ('Uber ride', 'Transport'),
    ('Bus fare ticket', 'Transport'),
    ('Car maintenance service', 'Transport'),
    ('Parking payment', 'Transport'),
    ('Electric bill payment', 'Utilities'),
    ('Internet subscription', 'Utilities'),
    ('Water bill', 'Utilities'),
    ('Mobile phone bill', 'Utilities'),
    ('Movie ticket', 'Entertainment'),
    ('Netflix subscription', 'Entertainment'),
    ('Concert ticket', 'Entertainment'),
    ('Steam game purchase', 'Entertainment'),
    ('Clothing purchase', 'Shopping'),
    ('Electronics from Best Buy', 'Shopping'),
    ('Shoe purchase', 'Shopping'),
    ('Book from Amazon', 'Shopping'),
    ('Gym membership', 'Health'),
    ('Doctor visit', 'Health'),
    ('Pharmacy medicine', 'Health'),
    ('Yoga class', 'Health'),
    ('Rent payment', 'Other'),
    ('Gift purchase', 'Other'),
    ('Home supplies', 'Other'),
]
