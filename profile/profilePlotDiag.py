
from qgis.PyQt import QtGui, uic
from PyQt4.Qwt5 import QwtPlot, QwtPlotZoomer, QwtPicker, QwtPlotPicker
from PyQt4.Qwt5 import QwtPlotGrid
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal, QSettings
from qgis.PyQt.QtGui import QSizePolicy, QPen, QColor, QStandardItemModel
from qgis.PyQt.QtGui import QPixmap, QIcon
from qgis.gui import QgsMapLayerComboBox, QgsMapLayerProxyModel
from qgis.gui import QgsFieldComboBox
import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'profileViewer.ui'))

FORM_CLASS2, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ExportSetting.ui'))


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
        self.fieldCombo.setEnabled(False)
        self.mdl = QStandardItemModel(0, 6)
        self.resetBtn.clicked.connect(self.setRescale)
        self.methodSelector.currentIndexChanged.connect(
            self.lockMapLayerSelector)
        self.setIcons()
        self.settingDiag = exportSettings()
        self.batchChecker.setEnabled(False)

        self.exportSettingBtn.clicked.connect(self.openExportSettings)
        self.layerCombo.layerChanged.connect(self.fieldCombo.setLayer)

    def lockMapLayerSelector(self, idx):
        if idx == 0:
            self.layerCombo.setEnabled(False)
            self.reActivateBtn.setEnabled(True)
            self.batchChecker.setEnabled(False)
            self.fieldCombo.setEnabled(False)
        elif idx == 1:
            self.layerCombo.setEnabled(True)
            self.reActivateBtn.setEnabled(False)
            self.batchChecker.setEnabled(True)
            self.fieldCombo.setEnabled(True)

    def openExportSettings(self):
        self.settingDiag.run()

    def setIcons(self):
        pixMap = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'settings.svg'))
        settingIcon = QIcon(pixMap)
        self.exportSettingBtn.setIcon(settingIcon)
        self.exportSettingBtn.setIconSize(0.085*pixMap.rect().size())

        pixMap2 = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'if_arrow-up.svg'))
        icon2 = QIcon(pixMap2)
        self.moveForwardBtn.setIcon(icon2)
        self.moveForwardBtn.setIconSize(self.moveForwardBtn.size())

        pixMap3 = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'if_arrow-down.svg'))
        icon3 = QIcon(pixMap3)
        self.moveBackwardBtn.setIcon(icon3)
        self.moveBackwardBtn.setIconSize(self.moveBackwardBtn.size())

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

        self.fieldCombo = QgsFieldComboBox()
        self.layoutForField.addWidget(self.fieldCombo)

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


class exportSettingDiag(QtGui.QDialog, FORM_CLASS2):
    def __init__(self, parent=None):
        super(exportSettingDiag, self).__init__(parent)
        self.setupUi(self)

        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        if not self.settings.value('profilePlotExport'):
            self.settings.setValue('profilePlotExport', '.png')
        else:
            _format = self.settings.value('profilePlotExport')
            idx = self.exportPicFormatBox.findText(_format)
            self.exportPicFormatBox.setCurrentIndex(idx)

        if not self.settings.value('profileTextExport'):
            self.settings.setValue('profileTextExport', '.txt')
        else:
            _format = self.settings.value('profileTextExport')
            idx = self.exportTextFormatBox.findText(_format)
            self.exportTextFormatBox.setCurrentIndex(idx)

        if self.settings.value('figureTitle'):
            self.titleEdit.setText(self.settings.value('figureTitle'))
        if self.settings.value('xAxisTitle'):
            self.xAxisEdit.setText(self.settings.value('xAxisTitle'))
        if self.settings.value('yAxisTitle'):
            self.yAxisEdit.setText(self.settings.value('yAxisTitle'))


class exportSettings:
    def __init__(self):
        self.dlg = exportSettingDiag()
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result == QtGui.QDialog.Accepted:
            self.settings.setValue('profilePlotExport',
                                   self.dlg.exportPicFormatBox.currentText())
            self.settings.setValue('profileTextExport',
                                   self.dlg.exportTextFormatBox.currentText())
            self.settings.setValue('figureTitle',
                                   self.dlg.titleEdit.text())
            self.settings.setValue('xAxisTitle',
                                   self.dlg.xAxisEdit.text())
            self.settings.setValue('yAxisTitle',
                                   self.dlg.yAxisEdit.text())
