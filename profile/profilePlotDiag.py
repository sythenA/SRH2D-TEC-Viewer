
from qgis.PyQt import QtGui, uic
from PyQt4.Qwt5 import QwtPlot, QwtPlotZoomer, QwtPicker, QwtPlotPicker
from PyQt4.Qwt5 import QwtPlotGrid
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal
from qgis.PyQt.QtGui import QSizePolicy, QPen, QColor, QStandardItemModel
from qgis.gui import QgsMapLayerComboBox, QgsMapLayerProxyModel
import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'profileViewer.ui'))


class profileViewerDialog(QtGui.QDialog, FORM_CLASS):
    closeWindow = pyqtSignal()

    def __init__(self, parent=None):
        super(profileViewerDialog, self).__init__(parent)
        self.setupUi(self)

        self.TecFileList.setItemHidden(self.TecFileList.headerItem(), True)
        self.TecFileList.clear()
        self.setPlotWidget()
        self.setLayerBoxWidget()
        self.layerCombo.setEnabled(False)
        self.mdl = QStandardItemModel(0, 6)
        self.resetBtn.clicked.connect(self.setRescale)
        self.methodSelector.currentIndexChanged.connect(
            self.lockMapLayerSelector)

    def lockMapLayerSelector(self, idx):
        if idx == 0:
            self.layerCombo.setEnabled(False)
        elif idx == 1:
            self.layerCombo.setEnabled(True)

    def setPlotWidget(self):
        self.plotWidget = QwtPlot(self.plotFrame)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.plotWidget.sizePolicy().hasHeightForWidth())
        self.plotWidget.setSizePolicy(sizePolicy)
        self.plotWidget.setMinimumSize(QSize(0, 0))
        self.plotWidget.setAutoFillBackground(False)
        self.plotWidget.setCanvasBackground(Qt.white)
        self.plotWidget.plotLayout().setAlignCanvasToScales(True)

        zoomer = QwtPlotZoomer(QwtPlot.xBottom, QwtPlot.yLeft,
                               QwtPicker.DragSelection, QwtPicker.AlwaysOff,
                               self.plotWidget.canvas())
        zoomer.setRubberBandPen(QPen(Qt.blue))
        # The pen to draw zone of zooming.

        picker = QwtPlotPicker(QwtPlot.xBottom, QwtPlot.yLeft,
                               QwtPicker.NoSelection,
                               QwtPlotPicker.CrossRubberBand,
                               QwtPicker.AlwaysOn, self.plotWidget.canvas())
        picker.setTrackerPen(QPen(Qt.green))
        grid = QwtPlotGrid()
        grid.setPen(QPen(QColor('grey'), 0, Qt.DotLine))
        grid.attach(self.plotWidget)

        layout = self.plotLayout
        layout.addWidget(self.plotWidget)

    def setLayerBoxWidget(self):
        self.layerCombo = QgsMapLayerComboBox()
        self.layerCombo.setFilters(QgsMapLayerProxyModel.LineLayer)
        layout = self.layerComboLayout
        layout.addWidget(self.layerCombo)

    def setRescale(self):
        self.plotWidget.setAxisAutoScale(0)
        self.plotWidget.setAxisAutoScale(2)
        self.plotWidget.replot()

    def closeEvent(self, event):
        self.closeWindow.emit()

        # Delete the icons under plugin folder
        folderPath = os.path.dirname(__file__)
        fileUnderFold = os.listdir(folderPath)

        for _file in fileUnderFold:
            if _file.endswith('.svg'):
                os.remove(os.path.join(folderPath, _file))
