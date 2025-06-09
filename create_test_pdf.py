from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta

def create_test_bank_statement():
    # Create a new PDF
    c = canvas.Canvas("test_statement.pdf", pagesize=letter)
    width, height = letter
    
    # Add header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Bank of Example - Monthly Statement")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "Account Number: XXXX-XXXX-1234")
    c.drawString(50, height - 100, "Statement Period: January 1 - January 31, 2024")
    
    # Add transactions header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 140, "Date")
    c.drawString(150, height - 140, "Description")
    c.drawString(400, height - 140, "Amount")
    
    # Add sample transactions including subscriptions
    c.setFont("Helvetica", 10)
    y_position = height - 170
    
    transactions = [
        ("2024-01-05", "NETFLIX.COM", "-15.99"),
        ("2024-01-07", "Grocery Store Purchase", "-125.43"),
        ("2024-01-10", "SPOTIFY PREMIUM", "-9.99"),
        ("2024-01-12", "AMAZON PRIME MEMBERSHIP", "-14.99"),
        ("2024-01-15", "Restaurant XYZ", "-45.67"),
        ("2024-01-18", "ADOBE CREATIVE CLOUD", "-54.99"),
        ("2024-01-20", "Gas Station", "-65.00"),
        ("2024-01-22", "APPLE ICLOUD+ STORAGE", "-2.99"),
        ("2024-01-25", "MICROSOFT 365 SUBSCRIPTION", "-9.99"),
        ("2024-01-28", "DISNEY PLUS", "-13.99"),
        ("2024-01-30", "Utility Bill - Electric", "-156.78"),
    ]
    
    for date, desc, amount in transactions:
        c.drawString(50, y_position, date)
        c.drawString(150, y_position, desc)
        c.drawString(400, y_position, amount)
        y_position -= 20
    
    # Save the PDF
    c.save()
    print("Test PDF created: test_statement.pdf")

if __name__ == "__main__":
    try:
        create_test_bank_statement()
    except ImportError:
        print("Please install reportlab first: pip install reportlab")
        print("Creating a simple text file instead...")
        
        # Create a simple text file as alternative
        with open("test_statement.txt", "w") as f:
            f.write("""Bank of Example - Monthly Statement
Account Number: XXXX-XXXX-1234
Statement Period: January 1 - January 31, 2024

Date        Description                     Amount
2024-01-05  NETFLIX.COM                     -15.99
2024-01-07  Grocery Store Purchase          -125.43
2024-01-10  SPOTIFY PREMIUM                 -9.99
2024-01-12  AMAZON PRIME MEMBERSHIP         -14.99
2024-01-15  Restaurant XYZ                  -45.67
2024-01-18  ADOBE CREATIVE CLOUD            -54.99
2024-01-20  Gas Station                     -65.00
2024-01-22  APPLE ICLOUD+ STORAGE           -2.99
2024-01-25  MICROSOFT 365 SUBSCRIPTION      -9.99
2024-01-28  DISNEY PLUS                     -13.99
2024-01-30  Utility Bill - Electric         -156.78
""")
        print("Test text file created: test_statement.txt")