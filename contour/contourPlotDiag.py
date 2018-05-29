
import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'contourPlot.ui'))


class contourGenDialog(QtGui.QDialog, FORM_CLASS):
    closeWindow = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(contourGenDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.currentLayers.setItemHidden(self.currentLayers.headerItem(), True)
        self.layersToDraw.setItemHidden(self.layersToDraw.headerItem(), True)

    def closeEvent(self, event):
        self.closeWindow.emit()
