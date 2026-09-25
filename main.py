import sys
from PyQt6.QtWidgets import QApplication
from gui.guiBuilder import userInputApp
from PyQt6.QtGui import QIcon

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("flowApp.png"))

window = userInputApp()

window.show()

sys.exit(app.exec())