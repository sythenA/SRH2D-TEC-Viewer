
import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import QSettings, Qt, QSize
from qgis.PyQt.QtGui import QListWidgetItem, QFileDialog, QImage, QColor
from qgis.PyQt.QtGui import QPixmap, QIcon, QPainter
from qgis.core import QgsMapLayerRegistry, QgsMapRenderer, QgsRectangle
from qgis.core import QgsMapLayer, QgsRasterPipe, QgsRasterFileWriter
import subprocess
from shutil import copyfile
import _winreg


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'animation.ui'))


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
                item = layerItem(layer, self.layerList)
                self.layerList.addItem(item)

    def layersRemoved(self, removedLayers):
        if removedLayers:
            for layerId in removedLayers:
                layer = self.registry.mapLayer(layerId)
                itemList = self.layerList.findItems(layer.name(),
                                                    Qt.MatchExactly)
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
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            self.workingFolder = QFileDialog.getExistingDirectory(
                directory=self.settings.value('projFolder'))
            self.renderLayers()
            self.settings.setValue('animeName', self.dlg.outputNameEdit.text())
            self.settings.setValue('animeLapse',
                                   int(self.dlg.timeLapseEdit.text()))
            self.genGif()
            self.genMp4()

    def renderLayers(self):
        self.renderedLayerList = list()
        for i in range(0, self.dlg.layerList.count()):
            item = self.dlg.layerList.item(i)
            layer = item.layer
            if layer.type() == QgsMapLayer.VectorLayer:
                picPath = self.vectorLayerRender(layer, str(i+1).zfill(3))
                self.renderedLayerList.append(picPath)
            elif layer.type() == QgsMapLayer.RasterLayer:
                picPath = self.rasterLayerRender(layer, str(i+1).zfill(3))
                self.renderedLayerList.append(picPath)

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
        reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        k = _winreg.OpenKey(reg, r'SOFTWARE\ImageMagick\Current')
        pathName = os.path.join(_winreg.QueryValueEx(k, 'BinPath')[0],
                                'magick.exe')

        lapse = int(self.dlg.timeLapseEdit.text())
        cmd = ['cmd', '/c', pathName, 'convert', '-loop', '0', '-delay',
               str(lapse)+'x1']
        for path in self.renderedLayerList:
            cmd.append(path)

        outName = self.dlg.outputNameEdit.text() + '.gif'

        cmd.append(os.path.join(self.workingFolder, outName))
        subprocess.Popen(cmd, shell=True)

    def genMp4(self):
        ffmpegPath = os.path.join(os.path.dirname(__file__),
                                  'ffmpeg.exe')

        lapse = int(self.dlg.timeLapseEdit.text())
        cmd = (ffmpegPath + ' -r' + ' 1/'+str(lapse) + ' -start_number' +
               ' 0' + ' -i ' +
               os.path.join(self.workingFolder, '%03d.tiff') + ' -c:v' +
               ' libx264' + ' -r' + ' 30' + ' -pix_fmt' + ' yuv420p ' +
               os.path.join(self.workingFolder,
                            self.dlg.outputNameEdit.text())+'.mp4'
               )
        subprocess.Popen(['cmd', '/c', 'del',
                          os.path.join(self.workingFolder
                                       , self.dlg.outputNameEdit.text())+'.mp4'])
        subprocess.call(cmd, shell=True)
