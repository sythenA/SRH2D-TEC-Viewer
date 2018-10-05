# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# Profile
# Copyright (C) 2012  Patrice Verchere
# -----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this progsram; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------
import qgis
from qgis.core import QgsMapLayer, QgsSpatialIndex, QgsPoint, QgsFeature
from qgis.core import QgsFeatureRequest, QgsRectangle, QgsGeometry

from qgis.PyQt.QtGui import QMessageBox


def withinBoundary(layer, point, featureId, closestFeature):
    # find the furthest bounding box borders
    closestFeature = layer.getFeatures(
        QgsFeatureRequest(featureId)).next()
    rect = closestFeature.geometry().boundingBox()

    dist_pX_rXmax = abs(point.x() - rect.xMaximum())
    dist_pX_rXmin = abs(point.x() - rect.xMinimum())
    if dist_pX_rXmax > dist_pX_rXmin:
        width = dist_pX_rXmax
    else:
        width = dist_pX_rXmin

    dist_pY_rYmax = abs(point.y() - rect.yMaximum())
    dist_pY_rYmin = abs(point.y() - rect.yMinimum())
    if dist_pY_rYmax > dist_pY_rYmin:
        height = dist_pY_rYmax
    else:
        height = dist_pY_rYmin

    # create the search rectangle
    rect = QgsRectangle()
    rect.setXMinimum(point.x() - width)
    rect.setXMaximum(point.x() + width)
    rect.setYMinimum(point.y() - height)
    rect.setYMaximum(point.y() + height)

    # retrieve all geometries into the search rectangle

    iter2 = layer.getFeatures(QgsFeatureRequest(rect))
    # find the nearest feature
    minDist = -1
    featureId = None
    point = QgsGeometry.fromPointXY(point)
    f = QgsFeature()
    while iter2.nextFeature(f):
        geom = f.geometry()
        distance = geom.distance(point)
        if minDist < 0 or distance < minDist:
            minDist = distance
            featureId = f.id()
    # get the closest feature
    try:
        closestFeature = layer.getFeatures(
            QgsFeatureRequest(featureId)).next()
        if featureId is None or layer.getFeatures(
           QgsFeatureRequest(featureId)).next(f) is False:
            closestFeature = None
    except:
        f = QgsFeature()
        closestFeature = layer.getFeatures(
            QgsFeatureRequest(featureId)).nextFeature(f)
        closestFeature = f
        if featureId is None or layer.getFeatures(
           QgsFeatureRequest(featureId)).nextFeature(f) is False:
            closestFeature = None

    return closestFeature


class SelectLineTool:
    def __init__(self, selectionMethod="feature"):
        """Selection mode can be feature or layer."""
        self.selectionMethod = selectionMethod

    def getPointTableFromSelectedLine(self, iface, tool, newPoints):
        closestFeatures = []
        layer = iface.activeLayer()
        if layer is None:
            QMessageBox.warning(iface.mainWindow(), "Closest Feature Finder",
                                "No vector layers selected")
            return None, closestFeatures

        # get the point coordinates in the layer's CRS
        point = tool.toLayerCoordinates(layer, QgsPoint(
            newPoints[0][0], newPoints[0][1]))
        closestFeatures = self.select_closest_feature(
                iface, layer, point)

        return layer, closestFeatures

    @staticmethod
    def checkIsLineLayer(layer):
        if layer is None or layer.type() != QgsMapLayer.VectorLayer:
            return False
        return layer.geometryType() == qgis.core.QgsWkbTypes.LineGeometry

    @staticmethod
    def select_closest_feature(iface, layer, point):
        """Returns a list with the closest feature in given layer."""
        # Create the index with the layers features
        layerindex = QgsSpatialIndex()
        # rajout
        f = QgsFeature()
        #
        iter = layer.getFeatures()
        while iter.nextFeature(f):
            layerindex.insertFeature(f)
        # get the feature which has the closest bounding box using the spatial
        # index
        nearest = layerindex.nearestNeighbor(point, 1)
        featureId = nearest[0] if len(nearest) > 0 else None
        closestFeature = QgsFeature()

        if featureId is None or layer.getFeatures(
           QgsFeatureRequest(featureId)).next() is False:
            closestFeature = None

        booltemp = layer.geometryType() != qgis.core.QgsWkbTypes.PointGeometry

        if booltemp and closestFeature is not None:
            closestFeature = withinBoundary(layer, point, featureId,
                                            closestFeature)

        return [closestFeature] if closestFeature else []

    @staticmethod
    def select_layer_features(iface, layer, point):
        """Returns a list with all the features in layer.

        iface, point are unused, kept to use
        the same function interface as select_closest_feature.
        """
        if layer:
            return [f for f in layer.getFeatures()]
        else:
            return []
