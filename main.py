"""
Main entry point for the Hybrid Teacher Scheduler
Greedy Initialization + Genetic Algorithm Optimization
"""

import os
import sys
import time

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

# ---------------------- #
#   APP ENTRY POINT      #
# ---------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
