# -*- coding: big5 -*-
"""
/***************************************************************************
 TECViewDialog
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

import os

import re
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import QSettings
from PyQt4.QtGui import QIcon, QPixmap
from qgis.gui import QgsColorRampComboBox
from qgis.core import QgsStyleV2

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'TECViewer_dialog_base.ui'))


class TECViewDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(TECViewDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.readSettings()
        self.loadIcon()

    def readSettings(self):
        try:
            settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')
            folder = settings.value('projFolder')
            self.projFolderEdit.setText(folder)
        except:
            pass

    def loadIcon(self):
        pixMap = QPixmap(os.path.join(os.path.dirname(__file__),
                                      'georeference.svg'))
        geoIcon = QIcon(pixMap)
        self.geoRefBtn.setIcon(geoIcon)
        self.geoRefBtn.setIconSize(0.7*pixMap.rect().size())

        pixMap = QPixmap(os.path.join(os.path.dirname(__file__),
                                      'settings.svg'))
        settingIcon = QIcon(pixMap)
        self.callSettingsBtn.setIcon(settingIcon)
        self.callSettingsBtn.setIconSize(0.1*pixMap.rect().size())


SETIING_DIAG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'TEC_setting.ui'))


class TECReadSettingDiag(QtGui.QDialog, SETIING_DIAG_CLASS):
    def __init__(self, parent=None):
        super(TECReadSettingDiag, self).__init__(parent)
        self.setupUi(self)
        self.colorRampSelector = QgsColorRampComboBox()
        self.setColorRampBox()
        self.colorRampSelector.setMinimumHeight(20)
        self.ColorRampLayout.addWidget(self.colorRampSelector)

        # Default value of raster grid resolution and same point distance.
        self.settings = QSettings('ManySplendid', 'SRH2D_TEC_Viewer')
        if not self.settings.value('resolution'):
            self.settings.setValue('resolution', 20.0)
        if not self.settings.value('min_Dist'):
            self.settings.setValue('min_Dist', 0.0001)
        if not self.settings.value('crs'):
            self.settings.setValue('crs', 3826)

        self.resolutionInput.setText(str(self.settings.value('resolution')))
        self.minDisInput.setText(str(self.settings.value('min_Dist')))

    def setColorRampBox(self):
        style = QgsStyleV2().defaultStyle()
        self.colorRampSelector.populate(style)
        self.colorRampSelector.insertItem(0, 'default')
        self.colorRampSelector.setCurrentIndex(0)
