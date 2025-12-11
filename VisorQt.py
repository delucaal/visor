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
from VisorUtils.VisorObjects import ROIObject, ImageObject, TractographyObject, SurfaceObject

from VisorUI.VisorVolumeControlsUI import VisorVolumeControlsUI
from VisorUI.VisorTractControlsUI import VisorTractControlsUI
from VisorUI.VisorROIControlsUI import VisorROIControlsUI

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

        self.rightBarWidget = self.findChild(QtWidgets.QWidget,'tabWidget')

        self.fodSubsampSlider = self.findChild(QtWidgets.QSlider,'fodSubsampSlider')

        self.deleteFODButton = self.findChild(QtWidgets.QPushButton,'deleteFODButton')
        
        #self.tractPropertiesContainer.setVisible(False)
        
        self.volumeControlsUI = VisorVolumeControlsUI(self)
        self.tractControlsUI = VisorTractControlsUI(self)
        self.roiControlsUI = VisorROIControlsUI(self)
        
    def _link_qt_actions(self):
        self.loadFODButton.clicked.connect(self._load_FOD_clicked)
        self.deleteFODButton.clicked.connect(self._delete_FOD_button)

        self.fodSubsampSlider.valueChanged.connect(self._fod_subsamp_slider_moved)

        self.volumeControlsUI._link_qt_actions()
        self.tractControlsUI._link_qt_actions()
        self.roiControlsUI._link_qt_actions()
        
    def _setup_ui(self):
        print('_setup_ui')
        if(self.cdir == ''):
            self.cdir = os.getcwd()

        self.fod_subsamp = 1

        self.target_vs = [1,1,1]
        
        self._link_qt_objects()        
        self._link_qt_actions()
        
        #with open("dark_theme.qss", "r") as f:
        #    qss = f.read()
        self.setStyleSheet(qdarkstyle.load_stylesheet())        
        
        #os.environ["VTK_GRAPHICS_BACKEND"] = "WEBGPU"
        #print("Backend:", vtk.vtkRenderWindow().GetClassName())
        
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
        ambient_light = vtk.vtkLight()
        ambient_light.SetLightTypeToSceneLight()
        ambient_light.SetIntensity(0.1)
        self.scene.AddLight(ambient_light)
        
        # Directional light
        scene_light = vtk.vtkLight()
        scene_light.SetLightTypeToSceneLight()
        scene_light.SetPosition(50, 50, 100)
        scene_light.SetFocalPoint(0, 0, 0)
        scene_light.SetIntensity(0.25)
        self.scene.AddLight(scene_light)
        
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
            self.roiControlsUI.ApplyROIsToTracts()
                
    def _delete_FOD_button(self,_button):
        if(len(ObjectsManager.fod_list) > 0):
            #self.scene.RemoveActor(ObjectsManager.fod_list[0])
            ObjectsManager.fod_list[0].RemoveActorFromScene()
            ObjectsManager.RemoveFODObject()

    def _fod_subsamp_slider_moved(self,_slider):
        self.fod_subsamp = int(self.fodSubsampSlider.value())
                        
    ## FOD related actions
    def _load_FOD_clicked(self, _button):
        print('Load FOD clicked')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*)", options=options)
        if fileName:
            print(fileName)
            Q = fileName[len(fileName)-4:len(fileName)]
            if(Q == '.nii' or Q == 'i.gz'):
                self.LoadFODandDisplay(fileName)
                        
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
            self.roiControlsUI.ApplyROIsToTracts()
        
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
                self.tractControlsUI.tractsListWidget.setCurrentRow(index)
                self.current_actor_properties = vtk.vtkProperty()
                self.current_actor_properties.DeepCopy(self.current_actor.GetProperty())
                ObjectsManager.tracts_list[index].ActorHighlightedProps()
                self.tractControlsUI.tractsListWidget.setCurrentRow(index)
                self.iren.Render()
                self._interactor_camera() # Tracts should not be moved
            else:
                # Probably it is an ROI
                index = ObjectsManager.IndexOfROIObject(NewPickedActor)
                if(index != -1):
                    print('Found ROI in list ' + str(index))
                else:
                    return
                
                #self.tractsList.setCurrentRow(index)
                self.roiControlsUI.roiListWidget.setCurrentRow(index)
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
        #fA.AddActorToScene(self.scene)
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
            elif('.gii' in f):
                surface = SurfaceObject()
                surface.InitializeFromGIFTI(f)
                ObjectsManager.AddSurfaceObject(surface)
                #self.scene.AddActor(surface.actor)
                surface.AddActorToScene(self.scene)
                
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
