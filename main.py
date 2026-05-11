# ============================================================
# DigiConfig Pro — Sistema de Aprovisionamiento de ONUs
# Digicable | Barinas, Venezuela
# ============================================================
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.run()
