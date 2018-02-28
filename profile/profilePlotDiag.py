
from PyQt4 import QtGui, uic
from PyQt4.Qwt5 import QwtPlot, QwtPlotZoomer, QwtPicker, QwtPlotPicker
from PyQt4.Qwt5 import QwtPlotGrid
from PyQt4.QtCore import Qt, QSize
from PyQt4.QtGui import QSizePolicy, QPen, QColor
import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'profileViewer.ui'))


class profileViewerDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(profileViewerDialog, self).__init__(parent)
        self.setupUi(self)

        self.TecFileList.setItemHidden(self.TecFileList.headerItem(), True)
        self.TecFileList.clear()
        self.activeLayerList.setShowGrid(False)
        self.setPlotWidget()

    def setPlotWidget(self):
        self.plotWidget = QwtPlot(self.plotFrame)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
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

        layout = self.plotFrame.layout()
        layout.addWidget(self.plotWidget)
