import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource relative to project root """
    try:
        # PyInstaller temp folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Project root (assumes this script is in helpers/ folder)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)
