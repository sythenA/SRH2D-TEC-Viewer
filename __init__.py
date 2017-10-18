# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TECView
                                 A QGIS plugin
 Reading the results of SRH2D TEC output
                             -------------------
        begin                : 2017-10-17
        copyright            : (C) 2017 by ManySplendid co.
        email                : yengtinglin@manysplendid.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TECView class from file TECView.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .TECViewer import TECView
    return TECView(iface)
