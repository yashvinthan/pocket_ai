import sys
import os

# Ensure the package is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from pocket_ai.main import main
    main()
