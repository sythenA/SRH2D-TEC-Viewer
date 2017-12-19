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
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QListWidgetItem
# Initialize Qt resources from file resources.py
# Import the code for the dialog
from TECViewer_dialog import TECViewDialog, Settings
from qgis.core import QgsCoordinateReferenceSystem
from qgis.gui import QgsGenericProjectionSelector
from itertools import izip as zip, count
from .TECSettings.TECSettings import TECSettings as TecSettings
from .tools.TECfile import TECfile
import os
import re
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
        self.settings = Settings
        self.all_Attrs = list()
        self.dlg = TECViewDialog()

        self.dlg.fileListWidget.clear()
        self.dlg.attributeList.clear()

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
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def selectProjFolder(self):
        try:
            presetFolder = self.dlg.projFolderEdit.text()
        except(KeyError):
            presetFolder = ''
        caption = 'Please choose a project folder'
        folderName = QFileDialog.getExistingDirectory(self.dlg, caption,
                                                      presetFolder)
        self.dlg.projFolderEdit.setText(folderName)

    def selectCrs(self):
        crsDiag = QgsGenericProjectionSelector()
        crsDiag.exec_()
        crsId = crsDiag.selectedCrsId()
        crsType = QgsCoordinateReferenceSystem.InternalCrsId
        self.systemCRS = QgsCoordinateReferenceSystem(crsId, crsType)

    def selectTECFile(self):
        Caption = 'Please select a _TEC_.dat file or multiple files'
        projFolder = self.dlg.projFolderEdit.text()
        filePathes = QFileDialog.getOpenFileNames(
            self.dlg, Caption, os.path.join(projFolder, 'sim'), "*.dat")
        for path in filePathes:
            fileWidget = TECfile(self.dlg.fileListWidget, 0, path, self.iface,
                                 setting=self.settings)
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

    def writeSettings(self):
        plugin_fol = os.path.dirname(__file__)
        f = open(os.path.join(plugin_fol, '_settings_'), 'r')
        dat = f.readlines()
        f.close()

        _settings = dict()
        for line in dat:
            line = re.split('=', line)
            _settings.update({line[0].strip(): line[1].strip()})

        proj_Fol = self.dlg.projFolderEdit.text()
        _settings.update({'last_proj': proj_Fol})
        self.settings = _settings

        f = open(os.path.join(plugin_fol, '_settings_'), 'w')
        keys = _settings.keys()
        for key in keys:
            f.write(key + ' = ' + _settings[key] + '\n')

        f.close()

    def loadTECfiles(self):
        projFolder = self.dlg.projFolderEdit.text()
        outFolder = os.path.join(projFolder, 'TECView')
        if not os.path.isdir(outFolder):
            os.system('mkdir ' + outFolder)
        for i in range(0, self.dlg.fileListWidget.count()):
            TECitem = self.dlg.fileListWidget.item(i)
            self.iface.messageBar().pushMessage(
                'generating ' + TECitem.fileName)
            TECitem.outDir = outFolder
            TECitem.iface = self.iface
            TECitem.export()
        self.writeSettings()
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
