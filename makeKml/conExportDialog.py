
import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'conExport.ui'))


class conExportDiag(QtGui.QDialog, FORM_CLASS):
    closeWindow = pyqtSignal()

    def __init__(self, parent=None):
        super(conExportDiag, self).__init__(parent)
        self.setupUi(self)
        folder = os.path.dirname(os.path.dirname(__file__))
        pixmap = QtGui.QPixmap(os.path.join(folder, 'Georeference.svg'))
        icon = QtGui.QIcon(pixmap)
        self.selectGeoRefBtn.setIcon(icon)
        self.selectGeoRefBtn.setIconSize(self.selectGeoRefBtn.size())

    def closeEvent(self, event):
        self.closeWindow.emit()
