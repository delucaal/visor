#!/usr/bin/env python3
from PyQt5 import QtWidgets, uic

class VisorVolumeControlsUI(object):
    def __init__(self, parent):
        self.loadVolumeButton = parent.findChild(QtWidgets.QPushButton,'loadVolume')
        self.unloadVolButton = parent.findChild(QtWidgets.QPushButton,'unloadVolButton')        
        self.volumesListWidget = parent.findChild(QtWidgets.QListWidget,'volumesListWidget')
        
        self.axialSlider = parent.findChild(QtWidgets.QSlider,'axialSlider')
        self.axialEdit = parent.findChild(QtWidgets.QLineEdit,'axialEdit')
        self.coronalSlider = parent.findChild(QtWidgets.QSlider,'coronalSlider')
        self.coronalEdit = parent.findChild(QtWidgets.QLineEdit,'coronalEdit')
        self.sagittalSlider = parent.findChild(QtWidgets.QSlider,'sagittalSlider')
        self.sagittalEdit = parent.findChild(QtWidgets.QLineEdit,'sagittalEdit')
        self.volTransparencySlider = parent.findChild(QtWidgets.QSlider,'volTransparencySlider')
        self.volMinValSlider = parent.findChild(QtWidgets.QSlider,'volMinValSlider')
        self.volMaxValSlider = parent.findChild(QtWidgets.QSlider,'volMaxValSlider')
        self.volMinValEdit = parent.findChild(QtWidgets.QLineEdit,'volMinValEdit')
        self.volMaxValEdit = parent.findChild(QtWidgets.QLineEdit,'volMaxValEdit')

        self.volColormapBox = parent.findChild(QtWidgets.QComboBox,'volColormapBox')
        for ij in self.available_colormaps:
            self.volColormapBox.addItem(ij)
            
        self.axialImageCheckBox = parent.findChild(QtWidgets.QCheckBox,'axialImageCheckBox')
        self.coronalImageCheckBox = parent.findChild(QtWidgets.QCheckBox,'coronalImageCheckBox')
        self.sagittalImageCheckBox = parent.findChild(QtWidgets.QCheckBox,'sagittalImageCheckBox')
        self.highlightedOnlyCheckbox = parent.findChild(QtWidgets.QCheckBox,'highlightedOnlyCheckbox')
            
            