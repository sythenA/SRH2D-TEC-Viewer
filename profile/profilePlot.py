
from profilePlotDiag import profileViewerDialog
from ..tools.TECBoxItem import TECBoxItem, layerItem


class profilePlot:
    def __init__(self, iface, TEC_Container):
        self.iface = iface
        self.dlg = profileViewerDialog()
        self.setLayerList(TEC_Container)

        #  ---Signals Connections---
        self.dlg.TecFileList.itemChanged.connect(self.setLayerState)

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass

    def setLayerList(self, TEC_Container):
        for item in TEC_Container:
            self.dlg.TecFileList.addTopLevelItem(
                TECBoxItem(self.dlg.TecFileList, item))

    def setLayerState(self, item, idx):
        item.doAsState()
