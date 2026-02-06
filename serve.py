"""Production launcher for Study-Notion server."""
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from main import create_app

app = create_app()

if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  Study-Notion Server Running")
    print(f"  Local:   http://127.0.0.1:5000")
    print(f"  Network: http://0.0.0.0:5000")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
