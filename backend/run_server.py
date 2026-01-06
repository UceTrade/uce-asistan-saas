"""
UceAsistan - New Modular Server Launcher
Run this instead of start_server.py for the refactored architecture
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from core.server import main

if __name__ == "__main__":
    main()
