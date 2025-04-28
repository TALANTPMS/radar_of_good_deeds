from flask import Flask
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app, db
except Exception as e:
    print(f"Import error: {e}")

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Database initialization error: {str(e)}")

app.debug = False
application = app

if __name__ == '__main__':
    app.run()
