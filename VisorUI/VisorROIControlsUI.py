#!/usr/bin/env python3

import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QApplication

import vtk
from fury import actor,colormap
import os

from VisorUtils.ObjectsManagement import ObjectsManager
from VisorUtils.VisorObjects import ROIObject, ImageObject, TractographyObject
from VisorUI.VisorTractControlsUI import VisorTractControlsUI

class VisorROIControlsUI(object):
    shared = None
    
    def __init__(self,parent):
        VisorROIControlsUI.shared = self
        self.mainapp = parent

        self.roiListWidget = parent.findChild(QtWidgets.QListWidget,'ROIsListWidget')
        self.ROIsTreeWidget = parent.findChild(QtWidgets.QTreeWidget,'ROIsTreeWidget')

        self.roiXposSpinbox = parent.findChild(QtWidgets.QSpinBox, 'XspinBox')
        self.roiYposSpinbox = parent.findChild(QtWidgets.QSpinBox, 'YspinBox')
        self.roiZposSpinbox = parent.findChild(QtWidgets.QSpinBox, 'ZspinBox')
        self.roiSizeSpinbox = parent.findChild(QtWidgets.QSpinBox, 'SspinBox')

        self.sphereROIButton = parent.findChild(QtWidgets.QPushButton, 'sphereROIButton')
        self.deleteROIButton = parent.findChild(QtWidgets.QPushButton, 'deleteROIButton')
        self.toggleROIButton = parent.findChild(QtWidgets.QPushButton, 'toggleROIButton')

        self.current_roi = 0

    def _link_qt_actions(self):
        self.roiListWidget.itemClicked.connect(self._roi_clicked)

        self.roiXposSpinbox.valueChanged.connect(self._roi_x_slider_changed)
        self.roiYposSpinbox.valueChanged.connect(self._roi_y_slider_changed)
        self.roiZposSpinbox.valueChanged.connect(self._roi_z_slider_changed)
        self.roiSizeSpinbox.valueChanged.connect(self._roi_size_slider_changed)

        self.sphereROIButton.clicked.connect(self._add_sphere_roi)
        self.deleteROIButton.clicked.connect(self._delete_ROI_button)
        self.toggleROIButton.clicked.connect(self._toggle_ROI_button)

    ## ROI related actions
    def _add_sphere_roi(self, _button):
        O = ROIObject()
        O.InitSphereROI(center=[0, 0, 0], radius=1)
        O.AddActorToScene(self.mainapp.scene)
        ObjectsManager.AddROIObject(O)
        ROI_Name = O.Name + ' (Disabled)'
        self.roiListWidget.addItem(ROI_Name)
        self.ROIsTreeWidget.topLevelItem(0).addChild(QtWidgets.QTreeWidgetItem([O.Name, O.Type]))
        self.mainapp.iren.Render()

    def _roi_clicked(self, _item):
        cR = self.roiListWidget.currentRow()
        print('_roi_clicked ' + str(cR))
        self.current_roi = cR
        self.roiXposSpinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[0]))
        self.roiYposSpinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[1]))
        self.roiZposSpinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[2]))
        self.roiSizeSpinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetRadius()))
        ObjectsManager.rois_list[cR].ActorHighlightedProps()

    def _roi_x_slider_changed(self, _item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]
        position = cR.source.GetCenter()
        position = [float(self.roiXposSpinbox.value()), position[1], position[2]]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.mainapp.iren.Render()

    def _roi_y_slider_changed(self, _item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]
        position = cR.source.GetCenter()
        position = [position[0], float(self.roiYposSpinbox.value()), position[2]]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.mainapp.iren.Render()

    def _roi_z_slider_changed(self, _item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]
        position = cR.source.GetCenter()
        position = [position[0], position[1], float(self.roiZposSpinbox.value())]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.mainapp.iren.Render()

    def _roi_size_slider_changed(self, _item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]
        size = self.roiSizeSpinbox.value()
        cR.source.SetRadius(size)
        cR.actor.Modified()
        self.mainapp.iren.Render()

    def _delete_ROI_button(self,_button):
        if(len(ObjectsManager.rois_list) > 0):
            #self.scene.RemoveActor(ObjectsManager.rois_list[self.troiListWidget.currentRow()].actor)
            ObjectsManager.rois_list[self.roiListWidget.currentRow()].RemoveActorFromScene()
            ObjectsManager.RemoveROIObject(self.roiListWidget.currentRow())
        self.ApplyROIsToTracts()

    def _toggle_ROI_button(self,_button):
        ObjectsManager.rois_list[self.roiListWidget.currentRow()].ToggleEnabled()
        if(ObjectsManager.rois_list[self.roiListWidget.currentRow()].enabled):
            # Activate the ROI and add it to the tract
            self.roisListWidget.currentItem().setText(ObjectsManager.rois_list[self.roiListWidget.currentRow()].Name + ' (Enabled)' )
            # First remove ROI from unassigned. Then, locate tract in tree top level widgets first, then add this children
            topLevelItem = self.ROIsTreeWidget.topLevelItem(0)
            for j in range(topLevelItem.childCount()):
                childItem = topLevelItem.child(j)
                if(childItem.text(0) == ObjectsManager.rois_list[self.roisListWidget.currentRow()].Name):
                    topLevelItem.removeChild(childItem)
                    break
            # Now add it to the right tract top item
            for i in range(1,self.ROIsTreeWidget.topLevelItemCount()):
                topLevelItem = self.ROIsTreeWidget.topLevelItem(i)
                if(topLevelItem.text(0) == VisorTractControlsUI.shared.tractsListWidget.currentItem().text()):
                    topLevelItem.addChild(childItem)
                    break
            ObjectsManager.tracts_list[VisorTractControlsUI.shared.tractsListWidget.currentRow()].AddROI(ObjectsManager.rois_list[self.roiListWidget.currentRow()])
        else:
            self.roisListWidget.currentItem().setText(ObjectsManager.rois_list[self.roiListWidget.currentRow()].Name + ' (Disabled)' )
            # Locate tract in tree top level widgets first, then look for this children and remove it
            # Deactivate the ROI and remove it from the tract
            for i in range(self.ROIsTreeWidget.topLevelItemCount()):
                topLevelItem = self.ROIsTreeWidget.topLevelItem(i)
                if(topLevelItem.text(0) == VisorTractControlsUI.shared.tractsListWidget.currentItem().text()):
                    for j in range(topLevelItem.childCount()):
                        childItem = topLevelItem.child(j)
                        if(childItem.text(0) == ObjectsManager.rois_list[self.roisListWidget.currentRow()].Name):
                            topLevelItem.removeChild(childItem)
                            self.ROIsTreeWidget.topLevelItem(0).addChild(childItem) # Unassigned
                            break
            ObjectsManager.tracts_list[VisorTractControlsUI.shared.tractsListWidget.currentRow()].DeleteROIByName(ObjectsManager.rois_list[self.roiListWidget.currentRow()].Name)
        self.ApplyROIsToTracts()

    def ApplyROIsToTracts(self):
        for tract in ObjectsManager.tracts_list:
            tract.color_tracts_by_roi_intersection_optimized(
                rois_list = None, #ObjectsManager.rois_list,
                #intersect_color = (1,0,0),
                alpha_outside = 0.3
            )
        self.mainapp.iren.Render()