# -*- coding: big5 -*-

from PyQt4.QtCore import QSettings, Qt, QSize
from PyQt4.QtGui import QPrinter, QPen, QPrintDialog, QPixmap, QFileDialog
from PyQt4.QtSvg import QSvgGenerator

from math import sqrt

from PyQt4.Qwt5 import QwtPlotCurve, QwtPlotMarker, QwtPlotItem
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
            vertLine.attach(wdg.plotWdg)
        profileLen = 0

    def attachCurves(self, wdg, profiles, model1):

        for i in range(0, model1.rowCount()):
            tmp_name = ("%s#%d") % (profiles[i]["layer"].name(),
                                    profiles[i]["band"]+1)

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

            # Create & attach one QwtPlotCurve per one single line
            for j in range(len(xx)):
                curve = QwtPlotCurve(tmp_name)
                curve.setData(xx[j], yy[j])
                curve.setPen(QPen(model1.item(i, 1).data(Qt.BackgroundRole), 3))
                curve.attach(wdg.plotWdg)
                if model1.item(i, 0).data(Qt.CheckStateRole):
                    curve.setVisible(True)
                else:
                    curve.setVisible(False)

            # scaling this
            try:
                wdg.setAxisScale(2, 0, max(profiles[len(profiles)-1]["l"]), 0)
                self.reScalePlot(wdg, profiles)
            except:
                pass
                # self.iface.mainWindow().statusBar().showMessage(
                # "Problem with setting scale of plotting")
        wdg.plotWdg.replot()

    def findMin(self, profiles, nr):
        minVal = min(z for z in profiles[nr]["z"] if z is not None)
        return minVal

    def findMax(self, profiles, nr):
        maxVal = max(z for z in profiles[nr]["z"] if z is not None) + 1
        return maxVal

    def reScalePlot(self, wdg, profiles, auto=False):
        # called when spinbox value changed
        if profiles is None:
            return
        minimumValue = wdg.sbMinVal.value()
        maximumValue = wdg.sbMaxVal.value()

        if minimumValue == maximumValue:
            # Automatic mode
            minimumValue = 1000000000
            maximumValue = -1000000000
            for i in range(0, len(profiles)):
                if (profiles[i]["layer"] != None and
                        len([z for z in
                             profiles[i]["z"] if z is not None]) > 0):

                    if self.findMin(profiles, i) < minimumValue:
                        minimumValue = self.findMin(profiles, i)
                    if self.findMax(profiles, i) > maximumValue:
                        maximumValue = self.findMax(profiles, i)
                    wdg.sbMaxVal.setValue(maximumValue)
                    wdg.sbMinVal.setValue(minimumValue)
                    wdg.sbMaxVal.setEnabled(True)
                    wdg.sbMinVal.setEnabled(True)

        if minimumValue < maximumValue:
            wdg.plotWdg.setAxisScale(0, minimumValue, maximumValue, 0)
            wdg.plotWdg.replot()

    def clearData(self, wdg, profiles):
        # erase one of profiles
        if not profiles:
            return

        wdg.plotWdg.clear()
        for i in range(0, len(profiles)):
            profiles[i]["l"] = []
            profiles[i]["z"] = []
        temp1 = wdg.plotWdg.itemList()
        for j in range(len(temp1)):
            if temp1[j].rtti() == QwtPlotItem.Rtti_PlotCurve:
                temp1[j].detach()
        # wdg.plotWdg.replot()

        wdg.sbMaxVal.setEnabled(False)
        wdg.sbMinVal.setEnabled(False)
        wdg.sbMaxVal.setValue(0)
        wdg.sbMinVal.setValue(0)

    def changeColor(self, wdg, color1, name):
        # Action when clicking the tableview - color
        temp1 = wdg.plotWdg.itemList()
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
