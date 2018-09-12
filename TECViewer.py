# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TECView
                                 A QGIS plugin
 Reading the results of SRH2D TEC output
                              -------------------
        begin                : 2017-10-17
        git sha              : $Format:%H$
        copyright            : (C) 2017 by ManySplendid co.
        email                : yengtinglin@manysplendid.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QListWidgetItem
from qgis.PyQt.QtGui import QMenu, QFileDialog
# Initialize Qt resources from file resources.py
# Import the code for the dialog
from TECViewer_dialog import TECViewDialog
from qgis.core import QgsCoordinateReferenceSystem
from qgis.gui import QgsGenericProjectionSelector
from itertools import izip as zip, count
from .TECSettings.TECSettings import TECSettings as TecSettings
from .tools.TECfile import TECfile, TEClayerBox
from .tools.toUnicode import toUnicode
from .profile.profilePlot import profilePlot
from .contour.contourPlot import contourPlot
from .makeKml.kmlExport import kmlExport
from .vectorPlot.vectorDiag import vecPlot
from .animation.makeAnimation import makeAnimation
import os
import resources


class TECView:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TECView_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SRH2D_TECViewer')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'TECView')
        self.toolbar.setObjectName(u'TECView')
        self.all_Attrs = list()
        self.dlg = TECViewDialog()

        self.dlg.fileListWidget.clear()
        self.dlg.attributeList.clear()
        self.dlg.progressBar.setVisible(False)

        # - Button Connections  - #
        self.dlg.selectProjFolder.clicked.connect(self.selectProjFolder)
        self.dlg.geoRefBtn.clicked.connect(self.selectCrs)
        self.dlg.addFileBtn.clicked.connect(self.selectTECFile)
        self.dlg.deleteFileBtn.clicked.connect(self.removeTECfile)
        self.dlg.fileListWidget.itemSelectionChanged.connect(self.showAttr)
        self.dlg.cancelLoadBtn.clicked.connect(lambda: self.dlg.done(0))
        self.dlg.attributeList.clicked.connect(self.selectToShow)
        self.dlg.loadTECBtn.clicked.connect(self.loadTECfiles)
        self.dlg.callSettingsBtn.clicked.connect(self.runSettings)
        self.dlg.fileListWidget.customContextMenuRequested.connect(
            self.subMenuOnFileList)
        self.animation = makeAnimation(self.iface)

        self.profiler = profilePlot(self.iface)
        self.contourPlot = contourPlot(self.iface)
        self.makeKml = kmlExport(self.iface)
        self.vecPlot = vecPlot(self.iface)
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')
        try:
            self.systemCRS = self.settings.value('crs')
        except(AttributeError):
            self.settings.setValue('crs', 3826)
            crsType = QgsCoordinateReferenceSystem.InternalCrsId
            self.systemCRS = QgsCoordinateReferenceSystem(3826, crsType)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TECView', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, status_tip=None,
                   whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TECView/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SRH2D Post-Processing TEC File Viewer and analyser.'
                         ),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path,
            text=self.tr(u'Profile Viewer'),
            callback=self.profiler.run,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path,
            text=self.tr(u'Plot Contour'),
            callback=self.contourPlot.run,
            parent=self.iface.mainWindow())

        self.add_action(
            icon_path,
            text=self.tr(u'Export to .kml'),
            callback=self.makeKml.run,
            parent=self.iface.mainWindow())

        flowDirIcon = os.path.join(os.path.dirname(__file__), 'navigation.png')
        self.add_action(
            flowDirIcon,
            text=self.tr(u'Flow Direction'),
            callback=self.vecPlot.run,
            parent=self.iface.mainWindow())

        animationIcon = os.path.join(os.path.dirname(__file__), 'film.png')
        self.add_action(
            animationIcon,
            text=self.tr(u'Make Aniamtion'),
            callback=self.animation.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SRH2D_TECViewer'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.settings.setValue(
                'projFolder',
                toUnicode(self.dlg.projFolderEdit.text()))
            profileDiag = profilePlot(
                self.iface,
                toUnicode(self.dlg.projFolderEdit.text()),
                TEC_Box=self.TEC_Container)
            profileDiag.run()

    def selectProjFolder(self):
        try:
            presetFolder = self.dlg.projFolderEdit.text()
        except(KeyError):
            presetFolder = ''
        caption = 'Please choose a project folder'
        folderName = QFileDialog.getExistingDirectory(self.dlg, caption,
                                                      presetFolder)
        self.dlg.projFolderEdit.setText(toUnicode(folderName))

    def selectCrs(self):
        crsDiag = QgsGenericProjectionSelector()
        crsDiag.exec_()
        crsId = crsDiag.selectedCrsId()
        if crsId:
            crsType = QgsCoordinateReferenceSystem.InternalCrsId
            self.systemCRS = QgsCoordinateReferenceSystem(crsId, crsType)
            self.settings.setValue('crs', self.systemCRS.postgisSrid())

    def selectTECFile(self):
        Caption = 'Please select a _TEC_.dat file or multiple files'
        projFolder = toUnicode(self.dlg.projFolderEdit.text())
        filePathes = QFileDialog.getOpenFileNames(
            self.dlg, Caption, os.path.join(projFolder, 'sim'), "*.dat")
        for path in filePathes:
            path = toUnicode(path)
            fileWidget = TECfile(self.dlg.fileListWidget, 0,
                                 toUnicode(path),
                                 self.iface)
            self.dlg.fileListWidget.addItem(fileWidget)

    def removeTECfile(self):
        selectedTEC = self.dlg.fileListWidget.currentItem()
        c_row = self.dlg.fileListWidget.row(selectedTEC)
        self.dlg.fileListWidget.takeItem(c_row)

    def showAttr(self):
        self.dlg.attributeList.clear()
        current = self.dlg.fileListWidget.currentItem()
        attributes = current.attributes
        for attr in attributes:
            item = QListWidgetItem(attr[0], self.dlg.attributeList)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            if attr[1] == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.dlg.attributeList.addItem(item)

    def changeAttrToOutput(self, TECitem, attr):
        idx = [r for r, j in zip(count(), TECitem.attributes) if attr in j][0]
        TECitem.attributes[idx][1] = 1

    def changeAttrToCancel(self, TECitem, attr):
        idx = [r for r, j in zip(count(), TECitem.attributes) if attr in j][0]
        TECitem.attributes[idx][1] = 0

    def selectToShow(self):
        attrList = self.dlg.attributeList
        for i in range(0, attrList.count()):
            attrItem = attrList.item(i)
            attrName = attrItem.text()
            if attrItem.checkState() == Qt.Checked:
                if self.dlg.chageAllBtn.isChecked():
                    for t in range(0, self.dlg.fileListWidget.count()):
                        TECitem = self.dlg.fileListWidget.item(t)
                        self.changeAttrToOutput(TECitem, attrName)
                else:
                    TECitem = self.dlg.fileListWidget.currentItem()
                    self.changeAttrToOutput(TECitem, attrName)
            else:
                if self.dlg.chageAllBtn.isChecked():
                    for t in range(0, self.dlg.fileListWidget.count()):
                        TECitem = self.dlg.fileListWidget.item(t)
                        self.changeAttrToCancel(TECitem, attrName)
                else:
                    TECitem = self.dlg.fileListWidget.currentItem()
                    self.changeAttrToCancel(TECitem, attrName)

    def loadTECfiles(self):
        projFolder = toUnicode(self.dlg.projFolderEdit.text())
        outFolder = os.path.join(projFolder, u'TECView')
        self.TEC_Container = list()
        if not os.path.isdir(outFolder):
            os.system('mkdir ' + outFolder.encode('big5'))
        self.attrs()
        for i in range(0, self.dlg.fileListWidget.count()):
            TECitem = self.dlg.fileListWidget.item(i)
            TECitem.outDir = outFolder
            TECitem.iface = self.iface
            TECitem.export()
            item = TEClayerBox(TECitem, self.all_Attrs)
            self.TEC_Container.append(item)

        self.dlg.done(1)

    def attrs(self):
        Attrs = list()
        if self.all_Attrs:
            for item in self.all_Attrs:
                if type(item) == str:
                    Attrs.append(item)
                else:
                    Attrs.append(item[0])
        else:
            self.all_Attrs = list()

        for t in range(0, self.dlg.fileListWidget.count()):
            TECitem = self.dlg.fileListWidget.item(t)
            for z in range(0, len(TECitem.attributes)):
                if TECitem.attributes[z][0] not in Attrs:
                    Attrs.append(TECitem.attributes[z][0])
                    self.all_Attrs.append(TECitem.attributes[z][0])

    def runSettings(self):
        self.attrs()
        diag = TecSettings(self.iface, self.all_Attrs)
        self.all_Attrs = diag.run()

    def subMenuOnFileList(self, pos):
        cursorPos = self.dlg.fileListWidget.mapToGlobal(pos)
        subMenu = QMenu()
        subMenu.addAction('Export', self.exportTEC)

        subMenu.exec_(cursorPos)

    def exportTEC(self):
        item = self.dlg.fileListWidget.currentItem()
        folder = os.path.dirname(item.filePath)
        tecName = item.fileName
        self.iface.messageBar().pushMessage('Export ' + tecName + ' to ' +
                                            folder)

        allItem = self.dlg.fileListWidget.selectedItems()
