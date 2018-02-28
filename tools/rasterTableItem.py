
from PyQt4.QtGui import QTableWidgetItem, QColor
from random import randint
import os


class profileAbleItem(QTableWidgetItem):
    def __init__(self, rasterName, rasterId, parent=None):
        super(profileAbleItem, self).__init__(parent, rasterName)
        self.setText(rasterName)
        self.randColor()

    def randColor(self):
        self.color = QColor(randint(1, 255),
                            randint(1, 255),
                            randint(1, 255), 255)
