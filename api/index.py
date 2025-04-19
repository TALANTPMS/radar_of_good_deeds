import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

if 'VERCEL' in os.environ:
    app.debug = False
    
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    app.run()
