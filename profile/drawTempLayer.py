
from qgis.gui import QgsMapTool
from qgis.core import QGis, QgsPoint
from qgis.PyQt.QtCore import pyqtSignal, Qt
import qgis.core
from qgis.PyQt.QtGui import QCursor
from callMapTool import profileSec


class plotCSTool:
    def __init__(self, profilePlotMain):
        self.profilePlotMain = profilePlotMain

        self.iface = self.profilePlotMain.iface
        self.canvas = self.profilePlotMain.iface.mapCanvas()
        self.tool = profilePlotMainMapTool(
            self.canvas, self.profilePlotMain)
        # the mouselistener
        self.pointstoDraw = []
        # Polyline in mapcanvas CRS analysed
        self.pointstoCal = []
        self.dblclktemp = None
        # enable disctinction between leftclick and doubleclick
        self.lastFreeHandPoints = []

        self.profileSec = profileSec(self.iface,
                                     self.profilePlotMain.dlg)

        self.textquit0 = "Click for polyline and double click to end (right \
click to cancel then quit)"
        self.textquit1 = "Select the polyline in a vector layer (Right click to\
 quit)"

        self.layerindex = None                            # for selection mode
        self.previousLayer = None                         # for selection mode


# ************************ Mouse listener actions ******************************

    def moved(self, position):
        # draw the polyline on the temp layer (rubberband)
        if len(self.pointstoDraw) > 0:
            # Get mouse coords
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
                position["x"], position["y"])
            # Draw on temp layer
            try:    # qgis2
                if QGis.QGIS_VERSION_INT >= 10900:
                    self.profilePlotMain.rubberband.reset(QGis.Line)
                else:
                    self.profilePlotMain.rubberband.reset(
                        self.profilePlotMain.polygon)
            except:  # qgis3
                self.profilePlotMain.rubberband.reset(
                    qgis.core.QgsWkbTypes.LineGeometry)

            for i in range(0, len(self.pointstoDraw)):
                self.profilePlotMain.rubberband.addPoint(
                        QgsPoint(self.pointstoDraw[i][0],
                                 self.pointstoDraw[i][1]))
            self.profilePlotMain.rubberband.addPoint(
                QgsPoint(mapPos.x(), mapPos.y()))

    def rightClicked(self, position):    # used to quit the current action
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
            position["x"], position["y"])
        newPoints = [[mapPos.x(), mapPos.y()]]
        # if newPoints == self.lastClicked:
        # return # sometimes a strange "double click" is given
        if len(self.pointstoDraw) > 0:
            self.pointstoDraw = []
            self.pointstoCal = []
            self.profilePlotMain.rubberband.reset(self.profilePlotMain.polygon)
            self.profilePlotMain.rubberbandbuf.reset()
            self.profilePlotMain.rubberbandpoint.hide()
        else:
            self.cleaning()

    def leftClicked(self, position):        # Add point to analyse
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
            position["x"], position["y"])
        newPoints = [[mapPos.x(), mapPos.y()]]
        """
        if self.profilePlotMain.doTracking:
            self.profilePlotMain.rubberbandpoint.hide()"""

        if newPoints == self.dblclktemp:
            self.dblclktemp = None
            return
        else:
            if len(self.pointstoDraw) == 0:
                self.profilePlotMain.rubberband.reset(
                    self.profilePlotMain.polygon)
                self.profilePlotMain.rubberbandbuf.reset()
            self.pointstoDraw += newPoints
        """
        if self.profilePlotMain.dockwidget.selectionmethod == 1:
            result = SelectLineTool().getPointTableFromSelectedLine(
                self.iface, self.tool, newPoints, self.layerindex,
                self.previousLayer, self.pointstoDraw)
            self.pointstoDraw = result[0]
            self.layerindex = result[1]
            self.previousLayer = result[2]
            # self.profilePlotMain.calculateProfil(self.pointstoDraw,
            # self.mdl,self.plotlibrary, False)
            self.profilePlotMain.calculateProfil(self.pointstoDraw, False)
            self.lastFreeHandPoints = self.pointstoDraw
            self.pointstoDraw = []
            self.iface.mainWindow().statusBar().showMessage(self.textquit1)
            """

    def doubleClicked(self, position):
        # if self.profilePlotMain.dockwidget.selectionmethod == 0:
        # Validation of line
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
            position["x"], position["y"])
        newPoints = [[mapPos.x(), mapPos.y()]]
        self.pointstoDraw += newPoints
        # launch analyses
        self.iface.mainWindow().statusBar().showMessage(
            str(self.pointstoDraw))
        self.profileSec.getProfile(self.pointstoDraw, self.tool)
        # Reset
        self.lastFreeHandPoints = self.pointstoDraw
        self.pointstoDraw = []
        # temp point to distinct leftclick and dbleclick
        self.dblclktemp = newPoints
        self.iface.mainWindow().statusBar().showMessage(self.textquit0)
        """
        if self.profilePlotMain.dockwidget.selectionmethod == 1:
            return"""

    def cleaning(self):            # used on right click
        try:
            # print str(self.previousLayer)
            self.previousLayer.removeSelection(False)
            # self.previousLayer.select(None)
        except:
            pass
        self.profilePlotMain.rubberbandpoint.hide()
        self.canvas.unsetMapTool(self.tool)
        self.canvas.setMapTool(self.profilePlotMain.saveTool)
        self.profilePlotMain.rubberband.reset(self.profilePlotMain.polygon)
        self.profilePlotMain.rubberbandbuf.reset()
        self.iface.mainWindow().statusBar().showMessage("")

    def connectTool(self):

        self.tool.moved.connect(self.moved)
        self.tool.rightClicked.connect(self.rightClicked)
        self.tool.leftClicked.connect(self.leftClicked)
        self.tool.doubleClicked.connect(self.doubleClicked)
        self.tool.desactivate.connect(self.deactivate)

        self.iface.mainWindow().statusBar().showMessage(self.textquit0)

    def deactivate(self):        # enable clean exit of the plugin

        self.tool.moved.disconnect(self.moved)
        self.tool.rightClicked.disconnect(self.rightClicked)
        self.tool.leftClicked.disconnect(self.leftClicked)
        self.tool.doubleClicked.disconnect(self.doubleClicked)
        self.tool.desactivate.disconnect(self.deactivate)
        self.profilePlotMain.rubberbandpoint.hide()
        self.profilePlotMain.rubberband.reset(self.profilePlotMain.polygon)

        self.iface.mainWindow().statusBar().showMessage("")


class profilePlotMainMapTool(QgsMapTool):

    moved = pyqtSignal(dict)
    rightClicked = pyqtSignal(dict)
    leftClicked = pyqtSignal(dict)
    doubleClicked = pyqtSignal(dict)
    desactivate = pyqtSignal()

    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.cursor = QCursor(Qt.CrossCursor)
        self.button = button

    def canvasMoveEvent(self, event):
        self.moved.emit({'x': event.pos().x(), 'y': event.pos().y()})

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rightClicked.emit({'x': event.pos().x(), 'y': event.pos().y()})
        else:
            self.leftClicked.emit({'x': event.pos().x(), 'y': event.pos().y()})

    def canvasDoubleClickEvent(self, event):
        self.doubleClicked.emit({'x': event.pos().x(), 'y': event.pos().y()})

    def activate(self):
        QgsMapTool.activate(self)
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        self.desactivate.emit()
        QgsMapTool.deactivate(self)

    def isZoomTool(self):
        return False

    def setCursor(self, cursor):
        self.cursor = QCursor(cursor)
