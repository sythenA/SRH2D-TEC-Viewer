# -*- coding: big5 -*-

from qgis.PyQt.QtCore import QSettings, Qt, QSize
from qgis.PyQt.QtGui import QPrinter, QPrintDialog, QPixmap, QFileDialog
from qgis.PyQt.QtGui import QBrush, QPainter
from qgis.PyQt.QtSvg import QSvgGenerator
from math import sqrt

from PyQt4.Qwt5 import QwtPlotCurve, QwtPlotItem, QwtPlotPrintFilter, QwtLegend
from PyQt4.Qwt5 import QwtPlot
import itertools  # only needed for Qwt plot
import os


class plotTool:
    settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')

    def attachCurves(self, wdg, profiles):
        for i in range(0, len(profiles)):
            tmp_name = ("%s") % (profiles[i]["layer"].name())

            # As QwtPlotCurve doesn't support nodata, split the data into
            # single lines
            # with breaks wherever data is None.
            # Prepare two lists of coordinates (xx and yy). Make x=None
            # whenever y is None.
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
        # self.resetScale(wdg, profiles)
        wdg.replot()

    def resetScale(self, wdg, profiles):
        if not profiles:
            return

        maxXVal = 0.
        minXVal = 1.0E8
        maxYVal = 0.
        minYVal = 1.0E8

        for i in range(0, len(profiles)):
            xx = profiles[i]["l"]
            yy = profiles[i]["z"]
            for j in range(len(yy)):
                if yy[j] is None:
                    xx[j] = None

            xx = [k for k in xx if k is not None]

            try:
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
            except(ValueError):
                pass

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

    def exportToTxt(self, profiles, f, title=''):
        # Generate Header
        if title:
            f.write(str(title)+'\n')
        line = ''
        line += ('{:<15s}'.format('Distance') + ' ')
        line += ('{:<15s}'.format('X_Coordinate') + ' ')
        line += ('{:<15s}'.format('Y_coordinate') + ' ')
        for profile in profiles:
            name = '{:<15s}'.format(profile['layer'].name())
            line += (name + ' ')
        line = line.rstrip() + '\n'
        f.write(line)

        for profile in profiles:
            if profile:
                L = profile['l']
                X = profile['x']
                Y = profile['y']
        try:
            L[0] = 0.
        except(IndexError):
            f.write('\n')
            return

        for j in range(1, len(L)):
            if not L[j]:
                L[j] = L[j-1] + sqrt((float(X[j])-float(X[j-1]))**2 +
                                     (float(Y[j])-float(Y[j-1]))**2)

        for i in range(0, len(X)):
            line = ''
            if type(L[i]) is float:
                line += ('{:<15.3f}'.format(L[i]) + ' ')
            elif type(L[i]) is str:
                line += ('{:<15s}'.format(L[i]) + ' ')
            elif not L[i]:
                line += ' '*16
            if type(X[i]) is float:
                line += ('{:<15.3f}'.format(X[i]) + ' ')
            elif type(X[i]) is str:
                line += ('{:<15s}'.format(X[i]) + ' ')
            if type(Y[i]) is float:
                line += ('{:<15.3f}'.format(Y[i]) + ' ')
            elif type(Y[i]) is str:
                line += ('{:<15s}'.format(Y[i]) + ' ')

            for profile in profiles:
                Z = profile['z']
                if type(Z[i]) is float:
                    line += ('{:<15.3f}'.format(Z[i]) + ' ')
                elif type(Z[i]) is str:
                    line += ('{:<15s}'.format(Z[i]) + ' ')
                elif not Z[i]:
                    line += ' '*16

            line = line.rstrip() + '\n'
            f.write(line)
        f.write('\n')

    def exportToCsv(self, profiles, f, title=''):
        # Generate Header
        if title:
            f.write(str(title)+'\n')
        line = ''
        line += ('Distance' + ',')
        line += ('X_Coordinate' + ',')
        line += ('Y_coordinate' + ',')
        for profile in profiles:
            name = profile['layer'].name()
            line += (name + ',')
        line = line[:-1] + '\n'
        f.write(line)

        for profile in profiles:
            if profile:
                L = profile['l']
                X = profile['x']
                Y = profile['y']
        try:
            L[0] = 0.
        except(IndexError):
            f.write('\n')
            return

        for j in range(1, len(L)):
            if not L[j]:
                L[j] = L[j-1] + sqrt((float(X[j])-float(X[j-1]))**2 +
                                     (float(Y[j])-float(Y[j-1]))**2)

        for i in range(0, len(X)):
            line = ''
            if L[i]:
                line += (str(L[i]) + ',')
            else:
                line += '  ,'
            if X[i]:
                line += (str(X[i]) + ',')
            else:
                line += '  ,'
            if Y[i]:
                line += (str(Y[i]) + ',')
            else:
                line += ' ,'

            for profile in profiles:
                Z = profile['z']
                if Z[i]:
                    line += (str(Z[i]) + ',')
                else:
                    line += ' ,'
            line = line[:-1] + '\n'

            f.write(line)
        f.write('\n')

    def exportToXls(self, profiles, sh, title=''):
        if title:
            sh.write(0, 0, str(title))

        sh.write(1, 0, 'Distance')
        sh.write(1, 1, 'X_Coordinate')
        sh.write(1, 2, 'Y_Coordinate')
        counter = 3
        for profile in profiles:
            sh.write(1, counter, profile['layer'].name())
            counter += 1

        for profile in profiles:
            if profile:
                X = profile['x']
                Y = profile['y']
                L = profile['l']

        try:
            L[0] = 0.
        except(IndexError):
            return

        for j in range(1, len(L)):
            if not L[j]:
                L[j] = L[j-1] + sqrt((float(X[j])-float(X[j-1]))**2 +
                                     (float(Y[j])-float(Y[j-1]))**2)
        for i in range(0, len(X)):
            sh.write(2+i, 0, float(L[i]))
            sh.write(2+i, 1, float(X[i]))
            sh.write(2+i, 2, float(Y[i]))
            counter = 3
            for profile in profiles:
                Z = profile['z']
                if Z[i]:
                    sh.write(2+i, counter, float(Z[i]))
                counter += 1

    def outSVG(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.svg')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .svg file",
                directory=folder,
                filter="Scalable Vector Graphics(*.svg)")

        if fileName:
            pix = QSvgGenerator()
            pix.setFileName(fileName)
            pix.setSize(QSize(600, 400))

            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)

    def outPNG(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.png')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .png file",
                directory=folder,
                filter="Portable Network Graphics (*.png)")

        if fileName:
            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            pix = QPixmap(QSize(600, 400))
            sh = QBrush(pix)
            sh.setColor(Qt.white)
            sh.setStyle(Qt.SolidPattern)
            painter = QPainter()
            painter.begin(pix)
            painter.setBrush(sh)
            painter.drawRect(0, 0, 600, 400)
            painter.end()

            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            pix.save(fileName)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)

    def outJPG(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.jpg')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .jpg file",
                directory=folder,
                filter="JPEG(*.jpg;*.jpeg)")

        if fileName:
            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            pix = QPixmap(QSize(600, 400))
            sh = QBrush(pix)
            sh.setColor(Qt.white)
            sh.setStyle(Qt.SolidPattern)
            painter = QPainter()
            painter.begin(pix)
            painter.setBrush(sh)
            painter.drawRect(0, 0, 600, 400)
            painter.end()

            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            pix.save(fileName)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)

    def outBMP(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.bmp')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .bmp file",
                directory=folder,
                filter="bitmap (*.bmp)")

        if fileName:
            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            pix = QPixmap(QSize(600, 400))
            sh = QBrush(pix)
            sh.setColor(Qt.white)
            sh.setStyle(Qt.SolidPattern)
            painter = QPainter()
            painter.begin(pix)
            painter.setBrush(sh)
            painter.drawRect(0, 0, 600, 400)
            painter.end()

            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            pix.save(fileName)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)

    def outTIF(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.tif')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .tif file",
                directory=folder,
                filter="Tagged Image File Format (*.tif;*.tiff)")

        if fileName:
            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            pix = QPixmap(QSize(600, 400))
            sh = QBrush(pix)
            sh.setColor(Qt.white)
            sh.setStyle(Qt.SolidPattern)
            painter = QPainter()
            painter.begin(pix)
            painter.setBrush(sh)
            painter.drawRect(0, 0, 600, 400)
            painter.end()

            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            pix.save(fileName)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)

    def outXBM(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.xbm')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .xbm file",
                directory=folder,
                filter="X Bitmap (*.xbm)")

        if fileName:
            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            pix = QPixmap(QSize(600, 400))
            sh = QBrush(pix)
            sh.setColor(Qt.white)
            sh.setStyle(Qt.SolidPattern)
            painter = QPainter()
            painter.begin(pix)
            painter.setBrush(sh)
            painter.drawRect(0, 0, 600, 400)
            painter.end()

            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            pix.save(fileName)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)

    def outXPM(self, plotWidget, d_folder, name, title):
        if d_folder:
            fileName = os.path.join(d_folder, name+'.xpm')
        else:
            if self.settings.value('lastOutputDir'):
                folder = self.settings.value('lastOutputDir')
            else:
                folder = self.settings.value('projFolder')

            fileName = QFileDialog.getSaveFileName(
                caption="Save Plot As .xpm file",
                directory=folder,
                filter="X Pixmap (*.xpm)")

        if fileName:
            if not title:
                title = self.settings.value('figureTitle')
            plotWidget.setTitle(title)
            pix = QPixmap(QSize(600, 400))
            sh = QBrush(pix)
            sh.setColor(Qt.white)
            sh.setStyle(Qt.SolidPattern)
            painter = QPainter()
            painter.begin(pix)
            painter.setBrush(sh)
            painter.drawRect(0, 0, 600, 400)
            painter.end()

            legend = QwtLegend()
            plotWidget.insertLegend(legend)
            plotWidget.setAxisTitle(
                QwtPlot.xBottom, self.settings.value('xAxisTitle'))
            plotWidget.setAxisTitle(
                QwtPlot.yLeft, self.settings.value('yAxisTitle'))

            QSettings().setValue("lastOutputDir", os.path.dirname(fileName))
            filter = QwtPlotPrintFilter()
            filter.setOptions(QwtPlotPrintFilter.PrintAll
                              & ~QwtPlotPrintFilter.PrintBackground)
            plotWidget.print_(pix, filter)
            pix.save(fileName)
            plotWidget.insertLegend(None)
            plotWidget.setAxisTitle(QwtPlot.xBottom, None)
            plotWidget.setAxisTitle(QwtPlot.yLeft, None)
            plotWidget.setTitle(None)
