# -*-coding:utf-8-*-
import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import QSettings, Qt, QSize
from qgis.PyQt.QtGui import QListWidgetItem, QFileDialog, QImage, QColor
from qgis.PyQt.QtGui import QPixmap, QIcon, QPainter, QMessageBox, QFont
from qgis.core import QgsMapLayerRegistry, QgsMapRenderer, QgsRectangle
from qgis.core import QgsRasterPipe, QgsRasterFileWriter
from qgis.core import QgsComposition, QgsComposerMap, QgsComposerLabel
from qgis.core import QgsMapSettings, QgsComposerLegend, QgsProject
from qgis.core import QgsComposerScaleBar
from qgis.PyQt.QtXml import QDomDocument
from msg import msgZhTW
from ..tools.toUnicode import toUnicode
import subprocess
import _winreg


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'animation.ui'))

message = msgZhTW


class layerItem(QListWidgetItem):
    def __init__(self, layer, parent):
        super(layerItem, self).__init__(layer.name(), parent)
        self.layer = layer


class animationDiag(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(animationDiag, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

        pixMap1 = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'if_arrow-up.svg'))
        icon1 = QIcon(pixMap1)
        self.moveUpBtn.setIcon(icon1)
        self.moveUpBtn.setIconSize(self.moveUpBtn.size())

        pixMap2 = QPixmap(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'if_arrow-down.svg'))
        icon2 = QIcon(pixMap2)
        self.moveDownBtn.setIcon(icon2)
        self.moveDownBtn.setIconSize(self.moveDownBtn.size())
        self.timeLapseEdit.setText(str(self.settings.value('frameTimeLapse')))
        self.outputNameEdit.setText(self.settings.value('animeName'))
        self.timeLapseEdit.setText(str(self.settings.value('animeLapse')))

        self.registry = QgsMapLayerRegistry.instance()
        self.updateLayers()

        self.registry.legendLayersAdded.connect(self.newLayersAdded)
        self.registry.layersWillBeRemoved.connect(self.layersRemoved)
        self.moveUpBtn.clicked.connect(self.moveUp)
        self.moveDownBtn.clicked.connect(self.moveDown)

    def updateLayers(self):
        mapLayers = self.registry.mapLayers()
        if mapLayers:
            for layerId in mapLayers.keys():
                layer = self.registry.mapLayer(layerId)
                item = layerItem(layer, self.layerList)
                self.layerList.addItem(item)

    def newLayersAdded(self, newLayers):
        if newLayers:
            for layer in newLayers:
                try:
                    item = layerItem(layer, self.layerList)
                    self.layerList.addItem(item)
                except(TypeError):
                    pass

    def layersRemoved(self, removedLayers):
        if removedLayers:
            for layerId in removedLayers:
                layer = self.registry.mapLayer(layerId)
                try:
                    itemList = self.layerList.findItems(layer.name(),
                                                        Qt.MatchExactly)
                except(AttributeError):
                    return

                if itemList:
                    for item in itemList:
                        idx = self.layerList.row(item)
                        self.layerList.takeItem(idx)

    def moveUp(self):
        idx = self.layerList.currentRow()

        if idx-1 >= 0:
            item = self.layerList.takeItem(idx)
            self.layerList.insertItem(idx-1, item)

    def moveDown(self):
        idx = self.layerList.currentRow()

        if idx+1 <= self.layerList.count():
            item = self.layerList.takeItem(idx)
            self.layerList.insertItem(idx+1, item)


class makeAnimation:
    def __init__(self, iface):
        self.iface = iface
        self.dlg = animationDiag(self.iface)
        self.registry = QgsMapLayerRegistry.instance()
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

    def loadTemplate(self, template):
        '''Load a print composer template from provided filename argument

        Args:
          template: readable .qpt template filename

        Returns:
          myComposition: a QgsComposition loaded from the provided template
          mapSettings: a QgsMapSettings object associated with myComposition'''
        mapSettings = QgsMapSettings()
        myComposition = QgsComposition(mapSettings)
        # Load template from filename
        with open(template, 'r') as templateFile:
            myTemplateContent = templateFile.read()

        myDocument = QDomDocument()
        myDocument.setContent(myTemplateContent)
        myComposition.loadFromTemplate(myDocument)

        return myComposition, mapSettings

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result == 1:
            self.workingFolder = toUnicode(QFileDialog.getExistingDirectory(
                directory=self.settings.value('projFolder')))
            self.settings.setValue('animeName', self.dlg.outputNameEdit.text())
            self.settings.setValue('animeLapse',
                                   int(self.dlg.timeLapseEdit.text()))
            if self.workingFolder:
                # Load map export template from .qgs file
                # composer, mapSet = self.loadTemplate(template)
                self.renderLayers()

                if self.dlg.exportTypeCombo.currentText() == '.gif':
                    self.genGif()
                elif self.dlg.exportTypeCombo.currentText() == '.mp4':
                    self.genMp4()

    def renderLayers(self):
        self.renderedLayerList = list()
        for i in range(0, self.dlg.layerList.count()):
            item = self.dlg.layerList.item(i)
            layer = item.layer
            picName = self.layerRenderByComposer(layer, str(i+1).zfill(3))
            self.renderedLayerList.append(picName)
        self.showAllLayers()
        """
        if layer.type() == QgsMapLayer.VectorLayer:
            picPath = self.vectorLayerRender(layer, str(i+1).zfill(3))
            self.renderedLayerList.append(picPath)
        elif layer.type() == QgsMapLayer.RasterLayer:
            picPath = self.rasterLayerRender(layer, str(i+1).zfill(3))
            self.renderedLayerList.append(picPath)"""

    def buildLegendLayerTree(self, root, layers):
        for child in root.children():
            # if the child is a group node, not a layer
            if child.nodeType() == 0:
                child = self.buildLegendLayerTree(child, layers)
            else:  # if it is a layer
                if child.layer() not in layers:
                    root.removeChildNode(child)
        return root

    def layerRenderByComposer(self, layer, outName):
        self.hideOtherLayers(layer)
        mapRenderer = self.iface.mapCanvas().mapRenderer()
        mapRenderer.setLayerSet([layer.id()])
        c = QgsComposition(mapRenderer)
        c.setPlotStyle(QgsComposition.Print)
        c.setPaperSize(297, 210)
        c.setPrintResolution(300)

        x, y = 0, 0
        w, h = c.paperWidth(), c.paperHeight()
        composerMap = QgsComposerMap(c, x, y, w, h)
        composerMap.setMapCanvas(self.iface.mapCanvas())
        c.addItem(composerMap)

        legend = QgsComposerLegend(c)
        root = QgsProject.instance().layerTreeRoot().clone()
        root = self.buildLegendLayerTree(root, [layer])
        legend.modelV2().setRootGroup(root)
        legend.setItemPosition(250, 20)
        legend.setResizeToContents(True)
        c.addItem(legend)

        label = QgsComposerLabel(c)
        label.setMarginX(125)
        label.setMarginY(10)
        label.setText(layer.name())
        label.setFont(QFont('PMinliu', 20, QFont.Bold))
        label.adjustSizeToText()
        c.addItem(label)

        item = QgsComposerScaleBar(c)
        item.setStyle('Double Box')  # optionally modify the style
        item.setComposerMap(composerMap)
        item.applyDefaultSize()
        item.setItemPosition(10, 190)
        c.addItem(item)

        dpmm = 300/25.4
        width = int(dpmm * c.paperWidth())
        width = int(width/2)*2
        height = int(dpmm * c.paperHeight())
        height = int(height/2)*2
        Dots = int(dpmm*1000/2)*2

        # create output image and initialize it
        image = QImage(QSize(width, height), QImage.Format_ARGB32)
        image.setDotsPerMeterX(Dots)
        image.setDotsPerMeterY(Dots)
        image.fill(0)

        # render the composition
        imagePainter = QPainter(image)
        c.renderPage(imagePainter, 0)
        imagePainter.end()

        outName = os.path.join(self.workingFolder, outName+'.png')
        image.save(outName, "png")

        return outName

    def hideOtherLayers(self, layer):
        allMapLayers = self.registry.mapLayers()
        for key in allMapLayers.keys():
            _layer = self.registry.mapLayer(key)
            self.iface.legendInterface().setLayerVisible(_layer, False)

        self.iface.legendInterface().setLayerVisible(layer, True)
        self.iface.mapCanvas().refresh()

    def showAllLayers(self):
        for key in self.registry.mapLayers().keys():
            layer = self.registry.mapLayer(key)
            self.iface.legendInterface().setLayerVisible(layer, True)

    def vectorLayerRender(self, layer, outName):
        img = QImage(QSize(1600, 900), QImage.Format_ARGB32_Premultiplied)
        color = QColor(255, 255, 255)
        img.fill(color.rgb())

        p = QPainter()
        p.begin(img)
        p.setRenderHint(QPainter.Antialiasing)

        render = QgsMapRenderer()
        lst = [layer.id()]  # add ID of every layer
        render.setLayerSet(lst)

        # set extent
        rect = QgsRectangle(render.fullExtent())
        rect.scale(1.1)
        render.setExtent(rect)
        # set output size
        render.setOutputSize(img.size(), img.logicalDpiX())
        # do the rendering
        render.render(p)
        p.end()
        # save image
        path = os.path.join(self.workingFolder, outName + '.tiff')
        img.save(path, "tiff")

        return path

    def rasterLayerRender(self, layer, outName):
        extent = layer.extent()
        # width, height = layer.width(), layer.height()
        width = 1600
        height = 900
        renderer = layer.renderer()
        provider = layer.dataProvider()

        pipe = QgsRasterPipe()
        pipe.set(provider.clone())
        pipe.set(renderer.clone())

        path = os.path.join(self.workingFolder, outName + '.tiff')
        file_writer = QgsRasterFileWriter(path)

        file_writer.writeRaster(pipe,
                                width,
                                height,
                                extent,
                                layer.crs())
        return path

    def genGif(self):
        msg = QMessageBox()
        try:
            reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
            k = _winreg.OpenKey(reg, r'SOFTWARE\ImageMagick\Current')
            pathName = os.path.join(_winreg.QueryValueEx(k, 'BinPath')[0],
                                    'magick.exe')
        except(WindowsError):
            msg.setIcon(QMessageBox.Critical)
            msg = message['msg01']
            msg.setWindowTitle(message['msg02'])
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

            return None

        lapse = int(self.dlg.timeLapseEdit.text())
        cmd = ['cmd', '/c', toUnicode(pathName).encode('big5'), 'convert',
               '-loop', '0', '-delay', str(lapse)+'x1']
        for path in self.renderedLayerList:
            cmd.append(path)

        outName = self.dlg.outputNameEdit.text() + '.gif'

        cmd.append(
            toUnicode(os.path.join(self.workingFolder, outName)).encode('big5'))
        subprocess.call(cmd, shell=True)
        msg.setIcon(QMessageBox.Information)
        msg.setText(message['msg03'])
        msg.setWindowTitle(message['msg04'])
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def genMp4(self):
        msg = QMessageBox()
        ffmpegPath = os.path.join(os.path.dirname(__file__),
                                  'ffmpeg.exe')

        lapse = int(self.dlg.timeLapseEdit.text())
        cmd = (ffmpegPath + ' -r' + ' 1/'+str(lapse) + ' -start_number' +
               ' 0' + ' -i ' +
               toUnicode(os.path.join(self.workingFolder, '%03d.png')).encode('big5') +
               ' -c:v' + ' libx264' + ' -r' + ' 30' + ' -pix_fmt' +
               ' yuv420p ' +
               toUnicode(os.path.join(self.workingFolder,
                         self.dlg.outputNameEdit.text())).encode('big5')
               + '.mp4')
        subprocess.Popen(['cmd', '/c', 'del',
                          toUnicode(os.path.join(self.workingFolder,
                                       self.dlg.outputNameEdit.text())).encode('big5')
                          +'.mp4'])
        t = subprocess.call(cmd, shell=True)
        if t == 0:
            msg.setIcon(QMessageBox.Information)
            msg.setText(message['msg05'])
            msg.setWindowTitle(message['msg06'])
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif t == 1:
            msg.setIcon(QMessageBox.Critical)
            msg.setText(message['msg07'])
            msg.setWindowTitle(message['msg08'])
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
