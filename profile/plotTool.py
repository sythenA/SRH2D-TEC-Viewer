# -*- coding: big5 -*-

from PyQt4.QtCore import QSettings, Qt, QSize
from PyQt4.QtGui import QPrinter, QPrintDialog, QPixmap, QFileDialog
from PyQt4.QtSvg import QSvgGenerator
from math import sqrt

from PyQt4.Qwt5 import QwtPlotCurve, QwtPlotMarker, QwtPlotItem, QwtPlot
import itertools  # only needed for Qwt plot
import os


class plotTool:
    def drawVertLine(self, wdg, pointstoDraw):
        profileLen = 0
        for i in range(0, len(pointstoDraw)-1):
            x1 = float(pointstoDraw[i][0])
            y1 = float(pointstoDraw[i][1])
            x2 = float(pointstoDraw[i+1][0])
            y2 = float(pointstoDraw[i+1][1])
            profileLen = (sqrt(((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1))) +
                          profileLen)
            vertLine = QwtPlotMarker()
            vertLine.setLineStyle(QwtPlotMarker.VLine)
            vertLine.setXValue(profileLen)
            vertLine.attach(wdg)
        profileLen = 0

    def attachCurves(self, wdg, profiles):
        for i in range(0, len(profiles)):
            tmp_name = ("%s") % (profiles[i]["layer"].name())

            # As QwtPlotCurve doesn't support nodata, split the data into single
            # lines
            # with breaks wherever data is None.
            # Prepare two lists of coordinates (xx and yy). Make x=None whenever
            # y is None.
            xx = profiles[i]["l"]
            yy = profiles[i]["z"]
            for j in range(len(yy)):
                if yy[j] is None:
                    xx[j] = None

            # Split xx and yy into single lines at None values
            xx = [list(g) for k, g in itertools.groupby(xx, lambda x:x is None)
                  if not k]
            yy = [list(g) for k, g in itertools.groupby(yy, lambda x:x is None)
                  if not k]

            Cstyle = profiles[i]["style"]
            # Create & attach one QwtPlotCurve per one single line
            for j in range(len(xx)):
                curve = QwtPlotCurve(tmp_name)
                curve.setData(xx[j], yy[j])
                curve.setPen(Cstyle)
                curve.attach(wdg)

            # scaling this
            try:
                wdg.setAxisScale(2, 0, max(profiles[len(profiles)-1]["l"]), 0)
                self.resetScale(wdg, profiles)
            except:
                pass
                # self.iface.mainWindow().statusBar().showMessage(
                # "Problem with setting scale of plotting")
        self.resetScale(wdg, profiles)
        wdg.replot()

    def resetScale(self, wdg, profiles):
        if not profiles:
            return

        maxXVal = 0.
        minXVal = 1.0E8
        maxYVal = 0.
        minYVal = 1.0E8

        QwtPlot

        for i in range(0, len(profiles)):
            xx = profiles[i]["l"]
            yy = profiles[i]["z"]
            for j in range(len(yy)):
                if yy[j] is None:
                    xx[j] = None

            xx = [k for k in xx if k is not None]

            _maxXVal = max(xx)
            _minXVal = min(xx)
            _maxYVal = self.findMax(profiles, i)
            _minYVal = self.findMin(profiles, i)

            if _maxXVal > maxXVal:
                maxXVal = _maxXVal
            if _minXVal < minXVal:
                minXVal = _minXVal
            if _maxYVal > maxYVal:
                maxYVal = _maxYVal
            if _minYVal < minYVal:
                minYVal = _minYVal

        # Y Axis rescale
        if minYVal < maxYVal:
            wdg.setAxisScale(0, minYVal-0.1*maxYVal, maxYVal*1.1, 0.)
            wdg.replot()
        elif minYVal == maxYVal:
            wdg.setAxisScale(0, 0.0, 10.0, 0.)
            wdg.replot()

        # X Axis rescale
        if minXVal < maxXVal:
            wdg.setAxisScale(2, minXVal*0.9, maxXVal+0.1*minXVal, 0.)
            wdg.replot()
        elif minXVal == maxXVal:
            wdg.setAxisScale(2, 0.0, 100.0, 0.)
            wdg.replot()

    def findMin(self, profiles, nr):
        minVal = min(z for z in profiles[nr]["z"] if z is not None)
        return minVal

    def findMax(self, profiles, nr):
        maxVal = max(z for z in profiles[nr]["z"] if z is not None) + 1
        return maxVal

    def clearData(self, wdg, profiles):
        # erase one of profiles
        if not profiles:
            return

        wdg.clear()
        for i in range(0, len(profiles)):
            profiles[i]["l"] = []
            profiles[i]["z"] = []
        temp1 = wdg.itemList()
        for j in range(len(temp1)):
            if temp1[j].rtti() == QwtPlotItem.Rtti_PlotCurve:
                temp1[j].detach()

    def changeColor(self, wdg, color1, name):
        # Action when clicking the tableview - color
        temp1 = wdg.plotWidget.itemList()
        for i in range(len(temp1)):
            if name == str(temp1[i].title().text()):
                curve = temp1[i]
                curve.setPen(QPen(color1, 3))
                wdg.plotWdg.replot()
                # break
                # Don't break as there may be multiple curves with a common
                # name (segments separated with None values)

    def changeAttachCurve(self, wdg, bool, name):
        # Action when clicking the tableview - checkstate
        temp1 = wdg.plotWidget.itemList()
        for i in range(len(temp1)):
            if name == str(temp1[i].title().text()):
                curve = temp1[i]
                if bool:
                    curve.setVisible(True)
                else:
                    curve.setVisible(False)
                wdg.plotWdg.replot()
                break

    def outPrint(self, iface, wdg, mdl):
        # Postscript file rendering doesn't work properly yet.
        for i in range(0, mdl.rowCount()):
            if mdl.item(i, 0).data(Qt.CheckStateRole):
                name = str(mdl.item(i, 2).data(Qt.EditRole))
                # return
        fileName = QFileDialog.getSaveFileName(
            iface.mainWindow(), "Save As", "Profile of " + name +
            ".ps", "PostScript Format (*.ps)")
        if fileName:
            printer = QPrinter()
            printer.setCreator("QGIS Profile Plugin")
            printer.setDocName("QGIS Profile")
            printer.setOutputFileName(fileName)
            printer.setColorMode(QPrinter.Color)
            printer.setOrientation(QPrinter.Portrait)
            dialog = QPrintDialog(printer)
            if dialog.exec_():
                wdg.plotWdg.print_(printer)

    def outPDF(self, iface, wdg, mdl):
        for i in range(0, mdl.rowCount()):
            if mdl.item(i, 0).data(Qt.CheckStateRole):
                name = str(mdl.item(i, 2).data(Qt.EditRole))
                break
        fileName = QFileDialog.getSaveFileName(
            iface.mainWindow(), "Save As", "Profile of " + name +
            ".pdf", "Portable Document Format (*.pdf)")
        if fileName:
            printer = QPrinter()
            printer.setCreator('QGIS Profile Plugin')
            printer.setOutputFileName(fileName)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOrientation(QPrinter.Landscape)
            wdg.plotWdg.print_(printer)

    def outSVG(self, iface, wdg, mdl):
        for i in range(0, mdl.rowCount()):
            if mdl.item(i, 0).data(Qt.CheckStateRole):
                name = str(mdl.item(i, 2).data(Qt.EditRole))
        fileName = QFileDialog.getSaveFileName(
            parent=iface.mainWindow(), caption="Save As",
            directory=wdg.profiletoolcore.loaddirectory,
            # filter = "Profile of " + name + ".png",
            filter="Scalable Vector Graphics (*.svg)")

        if fileName:
            if isinstance(fileName, tuple):  # pyqt5 case
                fileName = fileName[0]

            wdg.profiletoolcore.loaddirectory = os.path.dirname(fileName)
            QSettings().setValue(
                "profiletool/lastdirectory", wdg.profiletoolcore.loaddirectory)

            printer = QSvgGenerator()
            printer.setFileName(fileName)
            printer.setSize(QSize(800, 400))
            wdg.plotWdg.print_(printer)

    def outPNG(self, iface, wdg, mdl):
        for i in range(0, mdl.rowCount()):
            if mdl.item(i, 0).data(Qt.CheckStateRole):
                name = str(mdl.item(i, 2).data(Qt.EditRole))
                # return
        fileName = QFileDialog.getSaveFileName(
            parent=iface.mainWindow(), caption="Save As",
            directory=wdg.profiletoolcore.loaddirectory,
            # filter = "Profile of " + name + ".png",
            filter="Portable Network Graphics (*.png)")

        if fileName:
            if isinstance(fileName, tuple):  # pyqt5 case
                fileName = fileName[0]

            wdg.profiletoolcore.loaddirectory = os.path.dirname(fileName)
            QSettings().setValue("profiletool/lastdirectory",
                                 wdg.profiletoolcore.loaddirectory)

            QPixmap.grabWidget(wdg.plotWdg).save(fileName, "PNG")
