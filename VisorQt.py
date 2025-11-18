# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:10:40 2020

@author: Alberto De Luca (alberto.deluca.06@gmail.com)
"""

import os
import nibabel as nib

# from dipy.data import get_sphere
# import dipy.reconst.shm as shm

import vtk
import numpy as np

import sys
from PyQt5 import QtWidgets, uic
from PyQt5 import Qt
from PyQt5.QtWidgets import QFileDialog, QApplication
import qdarkstyle

from fury import actor,colormap

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy

from VisorUtils.FODActor import visorFODActor
from VisorUtils.SimpleThreading import MethodInBackground
from VisorUtils.ObjectsManagement import ObjectsManager
from VisorUtils.IOManager import VisorIO
from VisorUtils.VisorObjects import ROIObject, ImageObject, TractographyObject

from VisorUI.VisorVolumeControlsUI import VisorVolumeControlsUI
from VisorUI.VisorTractControlsUI import VisorTractControlsUI

class VisorMainAppQt(QtWidgets.QMainWindow):
    window_open = False
    current_actor = 0
    current_actor_properties = 0
    cdir = ''
    
    def __init__(self):
        print('init')
        super(VisorMainAppQt,self).__init__()
        uic.loadUi('Visor_alt.ui',self)
        # self.show_m = window.ShowManager(title='Visor', size=(1200, 900))
        self.cdir = os.getcwd()
        
        self._setup_ui()
        
        self.show()
        self.iren.Start()
        self.setAcceptDrops(True)
        
    def _link_qt_objects(self):
        self.renderFrame = self.findChild(QtWidgets.QFrame,'RenderFrame')
        self.loadFODButton = self.findChild(QtWidgets.QPushButton,'loadFODButton')

        self.roisListWidget = self.findChild(QtWidgets.QListWidget,'ROIsListWidget')

        self.rightBarWidget = self.findChild(QtWidgets.QWidget,'tabWidget')
        self.tractPropertiesContainer = self.findChild(QtWidgets.QTabWidget,'tractPropertiesContainer')

        self.fodSubsampSlider = self.findChild(QtWidgets.QSlider,'fodSubsampSlider')
        
        self.roiListWidget = self.findChild(QtWidgets.QListWidget,'ROIsListWidget')
        
        self.Xspinbox = self.findChild(QtWidgets.QSpinBox,'XspinBox')
        self.Yspinbox = self.findChild(QtWidgets.QSpinBox,'YspinBox')
        self.Zspinbox = self.findChild(QtWidgets.QSpinBox,'ZspinBox')
        self.Sspinbox = self.findChild(QtWidgets.QSpinBox,'SspinBox')
        
        self.sphereROIButton = self.findChild(QtWidgets.QPushButton,'sphereROIButton')
        self.deleteROIButton = self.findChild(QtWidgets.QPushButton,'deleteROIButton')
        self.toggleROIButton = self.findChild(QtWidgets.QPushButton,'toggleROIButton')
        
        self.deleteFODButton = self.findChild(QtWidgets.QPushButton,'deleteFODButton')
        
        self.ROIsTreeWidget = self.findChild(QtWidgets.QTreeWidget,'ROIsTreeWidget')
        #self.tractPropertiesContainer.setVisible(False)
        
        self.volumeControlsUI = VisorVolumeControlsUI(self)
        self.tractControlsUI = VisorTractControlsUI(self)
        
    def _link_qt_actions(self):
        self.loadFODButton.clicked.connect(self._load_FOD_clicked)
        self.deleteFODButton.clicked.connect(self._delete_FOD_button)
        
        self.roiListWidget.itemClicked.connect(self._roi_clicked)
        
        self.fodSubsampSlider.valueChanged.connect(self._fod_subsamp_slider_moved)
        
        self.Xspinbox.valueChanged.connect(self._roi_x_slider_changed)
        self.Yspinbox.valueChanged.connect(self._roi_y_slider_changed)
        self.Zspinbox.valueChanged.connect(self._roi_z_slider_changed)
        self.Sspinbox.valueChanged.connect(self._roi_size_slider_changed)

        self.sphereROIButton.clicked.connect(self._add_sphere_roi)
        self.deleteROIButton.clicked.connect(self._delete_ROI_button)
        self.toggleROIButton.clicked.connect(self._toggle_ROI_button)
        
        self.volumeControlsUI._link_qt_actions()
        self.tractControlsUI._link_qt_actions()
        
    def _setup_ui(self):
        print('_setup_ui')
        if(self.cdir == ''):
            self.cdir = os.getcwd()

        self.fod_subsamp = 1

        self.current_roi = 0
        self.target_vs = [1,1,1]
        
        self._link_qt_objects()        
        self._link_qt_actions()
        
        #with open("dark_theme.qss", "r") as f:
        #    qss = f.read()
        self.setStyleSheet(qdarkstyle.load_stylesheet())        
        
        self.vtkWidget = QVTKRenderWindowInteractor(self.renderFrame)       
        self.vl = Qt.QVBoxLayout()
        self.vl.addWidget(self.vtkWidget)
        self.scene = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.scene)
        self.scene.ResetCamera()
        #from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLRenderWindow
        #self.vtkWidget.GetRenderWindow().SetDebug(True)
        #self.scene.SetDebug(True)
        
        #self.rightBarWidget.setStyleSheet("QTabWidget::pane, QWidget { padding:0; margin:0; }")
        self.rightBarWidget.setContentsMargins(0, 0, 0, 0)
        
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.renderFrame.setLayout(self.vl)
        
        self.iren.Initialize()
        
        self.vtkWidget.GetRenderWindow().SetMultiSamples(8) 
        self.scene.UseFXAAOn()

        self.iren.AddObserver("LeftButtonPressEvent",self.leftButtonPressEvent)
        self.iren.AddObserver("KeyPressEvent",self.keyboardEvent)
        self._interactor_camera()
        
        # Renderer lights
        #self.scene.SetUseDepthPeeling(True)
        #self.scene.SetMaximumNumberOfPeels(100)
        #self.scene.SetOcclusionRatio(0.1)
        
        #headlight = vtk.vtkLight()
        #headlight.SetLightTypeToHeadlight()
        #self.scene.AddLight(headlight)

        # Optional ambient light
        #ambient_light = vtk.vtkLight()
        #ambient_light.SetLightTypeToSceneLight()
        #ambient_light.SetIntensity(0.3)
        #self.scene.AddLight(ambient_light)       
        
        # Directional light
        #scene_light = vtk.vtkLight()
        #scene_light.SetLightTypeToSceneLight()
        #scene_light.SetPosition(50, 50, 100)
        #scene_light.SetFocalPoint(0, 0, 0)
        #self.scene.AddLight(scene_light)         
        
        #self._add_sphere_roi(0)
        
        self.axes = vtk.vtkAxesActor()
        self.axes.SetTotalLength(400, 400, 400)  # length of X, Y, Z axes
        self.orientation_marker = vtk.vtkOrientationMarkerWidget()
        self.axes.SetShaftTypeToCylinder()
        self.axes.SetCylinderRadius(0.05)
        self.axes.SetConeRadius(0.2)
        self.orientation_marker.SetOrientationMarker(self.axes)
        self.orientation_marker.SetViewport(0.0, 0.0, .15, .15)  # bottom-left corner
        self.orientation_marker.SetInteractor(self.iren)  # your QVTKRenderWindowInteractor
        self.orientation_marker.EnabledOn()
        self.orientation_marker.InteractiveOff()
        
        camera = vtk.vtkCamera()
        camera.SetFocalPoint(0, 0, 0)

        distance = 100
        camera.SetPosition(0, 0, distance)
        camera.SetViewUp(0, 1, 0)

        # Assign the camera to the renderer
        self.scene.SetActiveCamera(camera)
        self.scene.ResetCameraClippingRange()  # adjust near/far planes
        #self.scene.AddActor(axes)
        
        self.ROIsTreeWidget.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Unassigned ROIs"]))
                
    def _interactor_camera(self):
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.style.SetCurrentRenderer(self.scene)
        self.style.SetInteractor(self.iren)
        self.iren.SetInteractorStyle(self.style)

    def _interactor_actor(self):
#        if(self.current_actor != 0 and self.current_actor is type(ROIObject)):
        self.style = vtk.vtkInteractorStyleTrackballActor()
        self.style.SetCurrentRenderer(self.scene)
        self.style.SetInteractor(self.iren)
        self.iren.SetInteractorStyle(self.style)
        self.iren.AddObserver("EndInteractionEvent", self.onInteractionEnd)
        
    def onInteractionEnd(self, obj, event):
        x, y = self.iren.GetEventPosition()
        picker = vtk.vtkPropPicker()
        picker.Pick(x, y, 0, self.scene)
        actor = picker.GetActor()
        if actor:
            self.ApplyROIsToTracts()
                
    def _delete_FOD_button(self,_button):
        if(len(ObjectsManager.fod_list) > 0):
            self.scene.RemoveActor(ObjectsManager.fod_list[0])            
            ObjectsManager.RemoveFODObject()
                                    
    ## ROI related actions
    def _add_sphere_roi(self,_button):
        O = ROIObject()
        O.InitSphereROI(center=[0,0,0],radius=1)
        self.scene.AddActor(O.actor)
        ObjectsManager.AddROIObject(O)
        ROI_Name = O.Name + ' (Disabled)'
        self.roiListWidget.addItem(ROI_Name)
        self.ROIsTreeWidget.topLevelItem(0).addChild(QtWidgets.QTreeWidgetItem([O.Name,O.Type]))
        self.iren.Render()
        
    def _roi_clicked(self,_item):
        cR = self.roiListWidget.currentRow()
        print('_roi_clicked ' + str(cR))
        self.current_roi = cR
        self.Xspinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[0]))
        self.Yspinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[1]))
        self.Zspinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[2]))
        self.Sspinbox.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetRadius()))
        ObjectsManager.rois_list[cR].ActorHighlightedProps()
                
    def _roi_x_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]   
        position = cR.source.GetCenter()
        position = [float(self.Xspinbox.value()),position[1],position[2]]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.iren.Render()
                          
    def _roi_y_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]   
        position = cR.source.GetCenter()
        position = [position[0],float(self.Yspinbox.value()),position[2]]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.iren.Render()

    def _roi_z_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]   
        position = cR.source.GetCenter()
        position = [position[0],position[1],float(self.Zspinbox.value())]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.iren.Render()
        
    def _roi_size_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR] 
        size = self.Sspinbox.value()  
        cR.source.SetRadius(size)
        cR.actor.Modified()
        self.iren.Render()
                                                                    
    def _fod_subsamp_slider_moved(self,_slider):
        self.fod_subsamp = int(self.fodSubsampSlider.value())
                        
    ## FOD related actions
    def _load_FOD_clicked(self, _button):
        print('Load FOD clicked')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);Python Files (*.py)", options=options)
        if fileName:
            print(fileName)
            Q = fileName[len(fileName)-4:len(fileName)]
            if(Q == '.nii' or Q == 'i.gz'):
                self.LoadFODandDisplay(fileName)
                        
    def _delete_ROI_button(self,_button):
        if(len(ObjectsManager.rois_list) > 0):
            self.scene.RemoveActor(ObjectsManager.rois_list[self.troiListWidget.currentRow()].actor)            
            ObjectsManager.RemoveROIObject(self.troiListWidget.currentRow())
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
                if(topLevelItem.text(0) == self.tractsListWidget.currentItem().text()):
                    topLevelItem.addChild(childItem) 
                    break                                                      
            ObjectsManager.tracts_list[self.tractsListWidget.currentRow()].AddROI(ObjectsManager.rois_list[self.roiListWidget.currentRow()])
        else:
            self.roisListWidget.currentItem().setText(ObjectsManager.rois_list[self.roiListWidget.currentRow()].Name + ' (Disabled)' )
            # Locate tract in tree top level widgets first, then look for this children and remove it
            # Deactivate the ROI and remove it from the tract
            for i in range(self.ROIsTreeWidget.topLevelItemCount()):
                topLevelItem = self.ROIsTreeWidget.topLevelItem(i)
                if(topLevelItem.text(0) == self.tractsListWidget.currentItem().text()):
                    for j in range(topLevelItem.childCount()):
                        childItem = topLevelItem.child(j)
                        if(childItem.text(0) == ObjectsManager.rois_list[self.roisListWidget.currentRow()].Name):
                            topLevelItem.removeChild(childItem)
                            self.ROIsTreeWidget.topLevelItem(0).addChild(childItem) # Unassigned
                            break
            ObjectsManager.tracts_list[self.tractsListWidget.currentRow()].DeleteROIByName(ObjectsManager.rois_list[self.roiListWidget.currentRow()].Name)
        self.ApplyROIsToTracts()

    def ApplyROIsToTracts(self):
        for tract in ObjectsManager.tracts_list:
            tract.color_tracts_by_roi_intersection_optimized(
                rois_list = None, #ObjectsManager.rois_list,
                #intersect_color = (1,0,0),
                alpha_outside = 0.3
            )
        self.iren.Render()

    def keyboardEvent(self,obj,event):
        key = self.iren.GetKeySym()
        if(key == 'm'):
            self._interactor_actor()
            print('Style actor')

        elif(key == 'o'):
            self._interactor_camera()
            if(len(ObjectsManager.rois_list) > 0):
                print(ObjectsManager.rois_list[-1].actor.GetCenter())
            if(len(ObjectsManager.tracts_list) > 0):
                print(ObjectsManager.tracts_list[-1].actor.GetCenter())
            print('Style camera')

        elif(key == 'i'):
            print('Intersection')
            self.ApplyROIsToTracts()
        
        elif(key == 'd'):
            self.set_view_3d()
        elif(key == 'a'):
            self.set_view_axial()
        elif(key == 'c'):
            self.set_view_coronal()
        elif(key == 's'):
            self.set_view_sagittal()
                
        print('Keyboard ' + key)

    def leftButtonPressEvent(self,obj,event):
        clickPos = self.iren.GetEventPosition()

        picker = vtk.vtkPropPicker()
        picker.Pick(clickPos[0], clickPos[1], 0, self.scene)
        
        # get the new
        NewPickedActor = picker.GetActor()
        
        # Restore properties of the previously picked actor
        if(self.current_actor != 0 and self.current_actor_properties != 0):
            self.current_actor.GetProperty().DeepCopy(self.current_actor_properties)
            self.current_actor = 0
            self.current_actor_properties = 0
            
        if(NewPickedActor != None):
            #if(NewPickedActor == self.current_actor):
            #    return
          
            self.current_actor = NewPickedActor
            # try:
            # index = ObjectsManager.tracts_list.index(NewPickedActor)
            index = ObjectsManager.IndexOfTractographyObject(NewPickedActor)
            if(index != -1):
                # It is a ctract
                print('Found tract in list ' + str(index))
                self.tractsListWidget.setCurrentRow(index)
                self.current_actor_properties = vtk.vtkProperty()
                self.current_actor_properties.DeepCopy(self.current_actor.GetProperty())
                ObjectsManager.tracts_list[index].ActorHighlightedProps()
                self.tractsListWidget.setCurrentRow(index)
                self.iren.Render()
                self._interactor_camera() # Tracts should not be moved
            else:
                # Probably it is an ROI
                index = ObjectsManager.IndexOfROIObject(NewPickedActor)
                if(index != -1):
                    print('Found ROI in list ' + str(index))
                #self.tractsList.setCurrentRow(index)
                self.roisListWidget.setCurrentRow(index)
                for roi in ObjectsManager.rois_list:
                    roi.ActorDefaultProps()
                ObjectsManager.rois_list[index].ActorHighlightedProps()
                self.iren.Render()
                self._interactor_actor() # ROIs can be moved
        else:
            for roi in ObjectsManager.rois_list:
                roi.ActorDefaultProps()            
            self._interactor_camera() # empty click -> default camera behavior

        # except:
            # print('Nothing to do')
        self.style.OnLeftButtonDown()
        
        # self.iren.Render()
        
    def LoadFODandDisplay(self, filename):

        fA = visorFODActor()
        fA.setRenderer(self.iren)
        fA.setTargetVoxelSize(self.target_vs)
        fA.loadFile(filename)
        ObjectsManager.AddFODObject(fA)
        
        # self.axialSlider.setMinimum(1)
        # self.axialSlider.setMaximum(fA.odf_data.shape[2])
        #fA.displayAxialFODs(self.axialSlider.value()) # automatically called from the slider
        
        self.scene.AddActor(fA)
        self.iren.Render()
        # self.scene.ResetCamera()
        # self.scene.ResetCameraClippingRange()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            print(f)
            if('.nii' in f):
                self.volumeControlsUI.LoadAndDisplayImage(f)
            elif('.mat' in f or '.trk' in f or '.tck' in f or '.vtk' in f):
                self.tractControlsUI.LoadAndDisplayTract(f)
                
    def get_scene_center(self):
        """Compute the center of the visible actors' bounding box."""
        bounds = [0]*6
        self.scene.ComputeVisiblePropBounds(bounds)
        cx = 0.5 * (bounds[0] + bounds[1])
        cy = 0.5 * (bounds[2] + bounds[3])
        cz = 0.5 * (bounds[4] + bounds[5])
        return cx, cy, cz


    def set_view_axial(self):
        """Top-down view (Z-axis) — radiological convention."""
        cam = self.scene.GetActiveCamera()
        cx, cy, cz = self.get_scene_center()
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(cx, cy, cz + 500)
        cam.SetViewUp(0, 1, 0)
        self.scene.ResetCamera()
        self.scene.GetRenderWindow().Render()


    def set_view_coronal(self):
        """Front view (Y-axis)."""
        cam = self.scene.GetActiveCamera()
        cx, cy, cz = self.get_scene_center()
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(cx, cy - 500, cz)
        cam.SetViewUp(0, 0, 1)
        self.scene.ResetCamera()
        self.scene.GetRenderWindow().Render()


    def set_view_sagittal(self):
        """Side view (X-axis)."""
        cam = self.scene.GetActiveCamera()
        cx, cy, cz = self.get_scene_center()
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(cx - 500, cy, cz)
        cam.SetViewUp(0, 0, 1)
        self.scene.ResetCamera()
        self.scene.GetRenderWindow().Render()


    def set_view_3d(self):
        """Oblique 3D perspective view."""
        cam = self.scene.GetActiveCamera()
        cx, cy, cz = self.get_scene_center()
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(cx + 400, cy - 400, cz + 300)
        cam.SetViewUp(0, 0, 1)
        self.scene.ResetCamera()
        self.scene.GetRenderWindow().Render()                
            
if __name__ == '__main__':
    vapp = QtWidgets.QApplication(sys.argv)
    window = VisorMainAppQt()
    sys.exit(vapp.exec_())
    sys.exit()#(vapp.exec_())
    quit()
    exit()
    # vapp.OpenWindow()
