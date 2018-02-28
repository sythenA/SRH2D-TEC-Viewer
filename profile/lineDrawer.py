
from PyQt4.QtGui import QgsMapTool, QCursor
from PyQt4.QtCore import pyqtSignal
from qgis.core import QGis, QgsPoint, Qt


class mapLineDraw:
    def __init__(self, iface, profileSec):
        self.iface = iface
        self.profileSec = profileSec
        self.iface = iface
        self.canvas = iface.mapCanvas()
        # Tack mouse position
        self.tool = ProfiletoolMapTool(self.canvas,
                                       self.profileSec.plugincore.action)
        self.pointstoDraw = []  # Polyline in mapcanvas CRS analysed
        self.pointstoCal = []
        # Enable disctinction between leftclick and doubleclick
        self.dblclktemp = None
        self.lastFreeHandPoints = []

        self.Text0 = "Left click to start draw profile (right click to cancel \
then quit)"

        self.layerindex = None                           # for selection mode
        self.previousLayer = None                        # for selection mode

# *************************** Mouse Tracking ***********************************
    # draw the polyline on the temp layer (rubberband)
    def moved(self, position):
        if self.profileSec.selectionmethod == 1:
            if len(self.pointstoDraw) > 0:
                # Get mouse coordinate
                mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
                    position["x"], position["y"])
                # Draw on temp layer
                self.profileSec.rubberband.reset(QGis.Line)

                for i in range(0, len(self.pointstoDraw)):
                    self.profileSec.rubberband.addPoint(QgsPoint(
                         self.pointstoDraw[i][0], self.pointstoDraw[i][1]))
                self.profileSec.rubberband.addPoint(
                    QgsPoint(mapPos.x(), mapPos.y()))
        if self.profileSec.dockwidget.selectionmethod == 0:
            return

    def rightClicked(self, position):    # used to quit the current action
        if self.profileSec.selectionmethod == 1:
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
                position["x"], position["y"])
            newPoints = [[mapPos.x(), mapPos.y()]]
            # if newPoints == self.lastClicked: return # sometimes a strange "double click" is given
            if len(self.pointstoDraw) > 0:
                self.pointstoDraw = []
                self.pointstoCal = []
                self.profileSec.rubberband.reset(False)
                self.profileSec.rubberbandbuf.reset()
                self.profileSec.rubberbandpoint.hide()
            else:
                self.cleaning()
        if self.profileSec.selectionmethod == 0:
            try:
                self.previousLayer.removeSelection(False)
            except:
                self.iface.mainWindow().statusBar().showMessage(
                    "error right click")
            self.cleaning()

    def leftClicked(self, position):        # Add point to analyse
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
            position["x"], position["y"])
        newPoints = [[mapPos.x(), mapPos.y()]]
        if self.profileSec.doTracking:
            self.profileSec.rubberbandpoint.hide()

        if self.profileSec.selectionmethod == 1:
            if newPoints == self.dblclktemp:
                self.dblclktemp = None
                return
            else:
                if len(self.pointstoDraw) == 1:
                    self.profiletool.rubberband.reset(self.profiletool.polygon)
                    self.profiletool.rubberbandbuf.reset()
                self.pointstoDraw += newPoints
            """
        if self.profileSec.selectionmethod == 0:
            result = SelectLineTool().getPointTableFromSelectedLine(
                self.iface, self.tool, newPoints, self.layerindex,
                self.previousLayer, self.pointstoDraw)

            self.pointstoDraw = result[0]
            self.layerindex = result[1]
            self.previousLayer = result[2]
            # self.profiletool.calculateProfil(self.pointstoDraw, self.mdl,self.plotlibrary, False)
            self.profileSec.getProfile(self.pointstoDraw, False)
            self.lastFreeHandPoints = self.pointstoDraw
            self.pointstoDraw = []
            self.iface.mainWindow().statusBar().showMessage(self.Text1)"""

    def doubleClicked(self, position):
        if self.profileSec.selectionmethod == 1:
            # Validation of line
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(
                position["x"], position["y"])
            newPoints = [[mapPos.x(), mapPos.y()]]
            self.pointstoDraw += newPoints
            # launch analyses
            self.iface.mainWindow().statusBar().showMessage(
                str(self.pointstoDraw))
            self.profileSec.getProfile(self.pointstoDraw)
            # Reset
            self.lastFreeHandPoints = self.pointstoDraw
            self.pointstoDraw = []
            # temporary point to distinct leftclick and dbleclick
            self.dblclktemp = newPoints
            self.iface.mainWindow().statusBar().showMessage(self.textquit0)
        if self.profiletool.dockwidget.selectionmethod == 0:
            return

    def cleaning(self):            # used on right click
        try:
            # print str(self.previousLayer)
            self.previousLayer.removeSelection(False)
            # self.previousLayer.select(None)
        except:
            pass
        self.profiletool.rubberbandpoint.hide()
        self.canvas.unsetMapTool(self.tool)
        self.canvas.setMapTool(self.profiletool.saveTool)
        self.profiletool.rubberband.reset(self.profiletool.polygon)
        self.profiletool.rubberbandbuf.reset()
        self.iface.mainWindow().statusBar().showMessage("")

    def connectTool(self):

        self.tool.moved.connect(self.moved)
        self.tool.rightClicked.connect(self.rightClicked)
        self.tool.leftClicked.connect(self.leftClicked)
        self.tool.doubleClicked.connect(self.doubleClicked)
        self.tool.desactivate.connect(self.deactivate)

        if self.profileSec.selectionmethod == 1:
            self.iface.mainWindow().statusBar().showMessage(self.textquit0)
        elif self.profileSec.selectionmethod == 0:
            self.iface.mainWindow().statusBar().showMessage(self.textquit1)

    def deactivate(self):        # enable clean exit of the plugin

        self.tool.moved.disconnect(self.moved)
        self.tool.rightClicked.disconnect(self.rightClicked)
        self.tool.leftClicked.disconnect(self.leftClicked)
        self.tool.doubleClicked.disconnect(self.doubleClicked)
        self.tool.desactivate.disconnect(self.deactivate)
        self.profiletool.rubberbandpoint.hide()
        self.profiletool.rubberband.reset(self.profiletool.polygon)

        self.iface.mainWindow().statusBar().showMessage("")


class ProfiletoolMapTool(QgsMapTool):

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
        self.button.setCheckable(True)
        self.button.setChecked(True)

    def deactivate(self):
        self.desactivate.emit()
        self.button.setCheckable(False)
        QgsMapTool.deactivate(self)

    def isZoomTool(self):
        return False

    def setCursor(self, cursor):
        self.cursor = QCursor(cursor)
