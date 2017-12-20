
from PyQt4 import QtGui, uic
import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'profileViewer.ui'))


class profileViewerDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(profileViewerDialog, self).__init__(parent)
        self.setupUi(self)
