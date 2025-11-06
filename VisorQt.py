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
from PyQt5.QtWidgets import QFileDialog

from fury import actor,colormap

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy

from VisorUtils.FODActor import visorFODActor
from VisorUtils.SimpleThreading import MethodInBackground
from VisorUtils.ObjectsManagement import ObjectsManager
from VisorUtils.IOManager import VisorIO
from VisorUtils.VisorObjects import ROIObject, ImageObject, TractographyObject

class VisorMainAppQt(QtWidgets.QMainWindow):
    window_open = False
    current_actor = 0
    current_actor_properties = 0
    cdir = ''
    available_colormaps = ('gray','viridis','plasma','inferno')
    
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
        # self.OpenWindow()
        
    def _link_qt_objects(self):
        self.renderFrame = self.findChild(QtWidgets.QFrame,'RenderFrame')
        self.loadVolumeButton = self.findChild(QtWidgets.QPushButton,'loadVolume')
        self.unloadVolButton = self.findChild(QtWidgets.QPushButton,'unloadVolButton')        
        self.loadFODButton = self.findChild(QtWidgets.QPushButton,'loadFODButton')
        self.loadSingleTractButton = self.findChild(QtWidgets.QPushButton,'loadSingleTract')
        self.loadAllTractsButton = self.findChild(QtWidgets.QPushButton,'loadAllTracts')
        self.deleteAllTractsButton = self.findChild(QtWidgets.QPushButton,'deleteAllTracts')
        self.deleteOneTractButton = self.findChild(QtWidgets.QPushButton,'deleteOneTractButton')
        self.deleteFODButton = self.findChild(QtWidgets.QPushButton,'deleteFODButton')
        self.clipCoronalButton = self.findChild(QtWidgets.QPushButton,'clipCoronalButton')
        self.deleteROIButton = self.findChild(QtWidgets.QPushButton,'deleteROIButton')
        self.toggleROIButton = self.findChild(QtWidgets.QPushButton,'toggleROIButton')

        self.tractsListWidget = self.findChild(QtWidgets.QListWidget,'tractsList')
        self.volumesListWidget = self.findChild(QtWidgets.QListWidget,'volumesListWidget')
        self.roisListWidget = self.findChild(QtWidgets.QListWidget,'ROIsListWidget')

        self.tractPropertiesContainer = self.findChild(QtWidgets.QTabWidget,'tractPropertiesContainer')
        self.axialSlider = self.findChild(QtWidgets.QSlider,'axialSlider')
        self.axialEdit = self.findChild(QtWidgets.QLineEdit,'axialEdit')
        self.coronalSlider = self.findChild(QtWidgets.QSlider,'coronalSlider')
        self.coronalEdit = self.findChild(QtWidgets.QLineEdit,'coronalEdit')
        self.sagittalSlider = self.findChild(QtWidgets.QSlider,'sagittalSlider')
        self.sagittalEdit = self.findChild(QtWidgets.QLineEdit,'sagittalEdit')
        self.volTransparencySlider = self.findChild(QtWidgets.QSlider,'volTransparencySlider')
        self.volMinValSlider = self.findChild(QtWidgets.QSlider,'volMinValSlider')
        self.volMaxValSlider = self.findChild(QtWidgets.QSlider,'volMaxValSlider')
        self.volMinValEdit = self.findChild(QtWidgets.QLineEdit,'volMinValEdit')
        self.volMaxValEdit = self.findChild(QtWidgets.QLineEdit,'volMaxValEdit')
        self.fodSubsampSlider = self.findChild(QtWidgets.QSlider,'fodSubsampSlider')
        
        self.tractColRedSlider = self.findChild(QtWidgets.QSlider,'tractColRedSlider')
        self.tractColGreenSlider = self.findChild(QtWidgets.QSlider,'tractColGreenSlider')
        self.tractColBlueSlider = self.findChild(QtWidgets.QSlider,'tractColBlueSlider')
        self.tractColAlphaSlider = self.findChild(QtWidgets.QSlider,'tractColAlphaSlider')
        self.tractThickSlider = self.findChild(QtWidgets.QSlider,'tractThickSlider')
        self.tractColDECButton = self.findChild(QtWidgets.QPushButton,'tractColDECButton')
        
        
        self.roiListWidget = self.findChild(QtWidgets.QListWidget,'ROIsListWidget')
        self.sphereROIButton = self.findChild(QtWidgets.QPushButton,'sphereROIButton')
        
        self.volColormapBox = self.findChild(QtWidgets.QComboBox,'volColormapBox')
        
        for ij in self.available_colormaps:
            self.volColormapBox.addItem(ij)
        
        self.axialImageCheckBox = self.findChild(QtWidgets.QCheckBox,'axialImageCheckBox')
        self.coronalImageCheckBox = self.findChild(QtWidgets.QCheckBox,'coronalImageCheckBox')
        self.sagittalImageCheckBox = self.findChild(QtWidgets.QCheckBox,'sagittalImageCheckBox')
        self.highlightedOnlyCheckbox = self.findChild(QtWidgets.QCheckBox,'highlightedOnlyCheckbox')

        self.tractsSubsamplingSlider = self.findChild(QtWidgets.QSlider,'subsamplingSlider')
        
        self.roiXSlider = self.findChild(QtWidgets.QSlider,'ROI_X_Slider')
        self.roiYSlider = self.findChild(QtWidgets.QSlider,'ROI_Y_Slider')
        self.roiZSlider = self.findChild(QtWidgets.QSlider,'ROI_Z_Slider')
        self.roiSizeSlider = self.findChild(QtWidgets.QSlider,'ROI_Size_Slider')
        #self.tractPropertiesContainer.setVisible(False)
        
    def _link_qt_actions(self):
        self.loadFODButton.clicked.connect(self._load_FOD_clicked)
        self.deleteFODButton.clicked.connect(self._delete_FOD_button)
        self.loadVolumeButton.clicked.connect(self._load_volume_clicked)
        self.unloadVolButton.clicked.connect(self._unload_volume_clicked)
        self.loadSingleTractButton.clicked.connect(self._file_clicked)
        self.loadAllTractsButton.clicked.connect(self._all_files_clicked)
        self.deleteAllTractsButton.clicked.connect(self._delete_all_tracts)
        self.deleteOneTractButton.clicked.connect(self._delete_one_tract)
        self.tractColDECButton.clicked.connect(self._tract_color_dec)
        self.sphereROIButton.clicked.connect(self._add_sphere_roi)
        self.deleteROIButton.clicked.connect(self._delete_ROI_button)
        self.toggleROIButton.clicked.connect(self._toggle_ROI_button)

        self.tractsListWidget.itemClicked.connect(self._track_clicked)
        self.volumesListWidget.itemClicked.connect(self._volume_clicked)
        self.roiListWidget.itemClicked.connect(self._roi_clicked)
        
        self.volColormapBox.activated.connect(self._volColormapSelected)

        self.axialSlider.valueChanged.connect(self._axial_slider_moved)
        self.axialEdit.editingFinished.connect(self._axial_slider_edit)
        self.coronalSlider.valueChanged.connect(self._coronal_slider_moved)
        self.sagittalSlider.valueChanged.connect(self._sagittal_slider_moved)
        
        self.volTransparencySlider.valueChanged.connect(self._transparency_slider_moved)
        self.volMinValSlider.valueChanged.connect(self._intensity_slider_moved)
        self.volMaxValSlider.valueChanged.connect(self._intensity_slider_moved)
        self.volMinValEdit.editingFinished.connect(self._intensity_edit)
        self.volMaxValEdit.editingFinished.connect(self._intensity_edit)
                
        self.fodSubsampSlider.valueChanged.connect(self._fod_subsamp_slider_moved)

        self.tractColRedSlider.valueChanged.connect(self._tract_color_slider_changed)
        self.tractColGreenSlider.valueChanged.connect(self._tract_color_slider_changed)
        self.tractColBlueSlider.valueChanged.connect(self._tract_color_slider_changed)
        self.tractColAlphaSlider.valueChanged.connect(self._tract_thick_slider_changed)
        self.tractThickSlider.valueChanged.connect(self._tract_thick_slider_changed)
        
        self.axialImageCheckBox.stateChanged.connect(self._axialimage_checkbox_state_changed)
        self.coronalImageCheckBox.stateChanged.connect(self._coronalimage_checkbox_state_changed)
        self.sagittalImageCheckBox.stateChanged.connect(self._sagittalimage_checkbox_state_changed)
        self.highlightedOnlyCheckbox.stateChanged.connect(self._highlight_checkbox_state_changed)
        
        self.tractsSubsamplingSlider.valueChanged.connect(self._tracts_subsampling_slider_moved)
        
        self.roiXSlider.valueChanged.connect(self._roi_x_slider_changed)
        self.roiYSlider.valueChanged.connect(self._roi_y_slider_changed)
        self.roiZSlider.valueChanged.connect(self._roi_z_slider_changed)
        self.roiSizeSlider.valueChanged.connect(self._roi_size_slider_changed)
        
    def _setup_ui(self):
        print('_setup_ui')
        if(self.cdir == ''):
            self.cdir = os.getcwd()

        self.axial_slice = 0
        self.sagittal_slice = 0
        self.coronal_slice = 0
        self.fod_subsamp = 1
        self.current_image = 0
        self.current_roi = 0
        self.target_vs = [1,1,1]
        
        self.show_axial_plane = True
        self.show_coronal_plane = True
        self.show_sagittal_plane = True

        self._link_qt_objects()        
        self._link_qt_actions()
        
        self.vtkWidget = QVTKRenderWindowInteractor(self.renderFrame)       
        self.vl = Qt.QVBoxLayout()
        self.vl.addWidget(self.vtkWidget)
        self.scene = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.scene)
        self.scene.ResetCamera()
        
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
        
        self._add_sphere_roi(0)
        #self._add_sphere_roi(0)
        #points = vtk.vtkPoints()
        #lines = vtk.vtkCellArray()
        #lines.InsertNextCell(3)
        #points.InsertNextPoint((-15,-15,-15))
        #lines.InsertCellPoint(0)
        #points.InsertNextPoint((0,0,0))
        #lines.InsertCellPoint(1)
        #points.InsertNextPoint((15,15,15))
        #lines.InsertCellPoint(2)
        #data = vtk.vtkPolyData()
        #data.SetPoints(points)
        #data.SetLines(lines)
        #self.test_line_s = data
        #self.test_line_source = vtk.vtkPolyLineSource()
        #self.test_line_source.SetNumberOfPoints(2)
        #self.test_line_source.SetPoints(points)
        #self.test_line_source.SetInputData(data)
        #self.test_line_source.SetOutput(data)

        #vtkm = vtk.vtkPolyDataMapper()
        #vtkm.SetInputConnection(self.test_line_source.GetOutputPort())#SetInputDataObject(data)
        #vtka = vtk.vtkActor()
        #vtka.SetMapper(vtkm)
        #self.scene.AddActor(vtka)
        #self.test_line_mapper = vtkm
                        
        #ObjectsManager.rois_list[-1].source.SetCenter((-5,-5,0))
        
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
        
    ## Tract related actions    
    def _track_clicked(self, _item):
        cR = self.tractsListWidget.currentRow()
        self.current_actor = ObjectsManager.tracts_list[cR].actor
        self.current_actor_properties = vtk.vtkProperty()
        self.current_actor_properties.DeepCopy(self.current_actor.GetProperty())
        self.current_actor.GetProperty().SetOpacity(1.0)
        self.iren.Render()

        print('_track_clicked ' + str(cR))
        #self.tractPropertiesContainer.setVisible(True)
        
        # Ensure tracts are only inspected and not moved
        self._interactor_camera()
            
    def _tract_color_slider_changed(self,_item):
        # if(self.current_actor != 0):
        print('_tract_color_slider_changed ' + str(self.tractColRedSlider.value()))
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]
        cR.SetColorSingle(red=self.tractColRedSlider.value(),
                                                 green=self.tractColGreenSlider.value(),
                                                 blue=self.tractColBlueSlider.value())
        cR.actor.GetProperty().SetOpacity(float(self.tractColAlphaSlider.value())/255.0)
        if(self.current_actor_properties != 0):
            self.current_actor_properties.DeepCopy(cR.actor.GetProperty())
        cR.actor.Modified()
        self.iren.Render()

    def _tract_color_dec(self,_button):
        print('_tract_color_dec')
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]
        cR.SetColorDEC()
        cR.actor.Modified()
        self.iren.Render()

    def _tract_thick_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]    
        cR.actor.GetProperty().SetLineWidth(self.tractThickSlider.value())
        cR.actor.GetProperty().SetOpacity(float(self.tractColAlphaSlider.value())/255.0)
        if(self.current_actor_properties != 0):
            self.current_actor_properties.DeepCopy(cR.actor.GetProperty())
        cR.actor.Modified()
        self.iren.Render()

    def _tracts_subsampling_slider_moved(self,_item):
        #print('_tracts_subsampling_slider_moved ' + str(self.tractsSubsamplingSlider.value()))
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]    
        factor = self.tractsSubsamplingSlider.value()
        if(factor < 1):
            factor = 1
        if(factor > 1):        
            cR.EnableUndersamplingWithFactor(factor)
        else:
            cR.DisableUndersampling()
        cR.actor.Modified()
        self.iren.Render()

    def _all_files_clicked(self, _button):
        print('Load all')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        the_dir = QFileDialog.getExistingDirectory(self,"QFileDialog.getOpenFileName()", options=options)
        A = os.listdir(the_dir)
        print(A)
        for SEL in A:
            Q = SEL[len(SEL)-4:len(SEL)]
            print(Q)
            if(Q == '.mat' or Q == '.MAT'):
                try:
                    self.LoadAndDisplayTract(the_dir + '/' + SEL,colorby='fe_seg')
                except:
                    print('Skipping ' + SEL + ' due to errors')
            
    def _delete_all_tracts(self, _button):
        print('delete tracts')
        for actor in ObjectsManager.tracts_list:
            self.scene.RemoveActor(actor.actor)
            
        ObjectsManager.RemoveTractographyObjects()
        self.tractsListWidget.clear()
        self.scene.ResetCamera()
        self.scene.ResetCameraClippingRange()
        
    def _delete_one_tract(self,_button):
        print('delete one tract')
        sel_items = self.tractsListWidget.selectedItems()        
        tracts_2_delete = []
        for item in sel_items:
            row = self.tractsListWidget.row(item)          
            tracts_2_delete.append(row)
        for zin in range(len(tracts_2_delete)-1,-1,-1):
            self.tractsListWidget.takeItem(tracts_2_delete[zin])
            self.scene.RemoveActor(ObjectsManager.tracts_list[zin].actor)
            ObjectsManager.RemoveTractographyObject(zin)
            
        self.iren.Render()
        
    ## ROI related actions
    def _add_sphere_roi(self,_button):
        O = ROIObject()
        O.InitSphereROI(center=[0,0,0],radius=1)
        self.scene.AddActor(O.actor)
        ObjectsManager.AddROIObject(O)
        ROI_Name = 'ROI_' + str(len(ObjectsManager.rois_list) + 1)
        self.roiListWidget.addItem(ROI_Name)
        
    def _roi_clicked(self,_item):
        cR = self.roiListWidget.currentRow()
        print('_roi_clicked ' + str(cR))
        self.current_roi = cR
        self.roiXSlider.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[0]))
        self.roiYSlider.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[1]))
        self.roiZSlider.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetCenter()[2]))
        self.roiSizeSlider.setValue(int(ObjectsManager.rois_list[self.current_roi].source.GetRadius()))
                
    def _roi_x_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]   
        position = cR.source.GetCenter()
        position = [self.roiXSlider.value()/1e1,position[1],position[2]]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.iren.Render()
                          
    def _roi_y_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]   
        position = cR.source.GetCenter()
        position = [position[0],self.roiYSlider.value()/1e1,position[2]]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.iren.Render()

    def _roi_z_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR]   
        position = cR.source.GetCenter()
        position = [position[0],position[1],self.roiZSlider.value()/1e1]
        cR.source.SetCenter(position)
        cR.actor.Modified()
        self.iren.Render()
        
    def _roi_size_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.roiListWidget.currentRow()
        cR = ObjectsManager.rois_list[cR] 
        size = self.roiSizeSlider.value()  
        cR.source.SetRadius(size)
        cR.actor.Modified()
        self.iren.Render()
                                                        
    ## Volume related actions
    def _volume_clicked(self,_item):
        cR = self.volumesListWidget.currentRow()
        print('volume_clicked ' + str(cR))
        self.current_image = cR
        self.UpdateImageSlice(which_image=self.current_image)
        self.volMinValSlider.setValue(ObjectsManager.images_list[self.current_image].minVal)
        self.volMaxValSlider.setValue(ObjectsManager.images_list[self.current_image].maxVal)
        self.volTransparencySlider.setValue(ObjectsManager.images_list[self.current_image].alpha)
        self.volColormapBox.setCurrentIndex(self.available_colormaps.index(ObjectsManager.images_list[self.current_image].colormap))
        
    def _unload_volume_clicked(self,_item):
        cR = self.volumesListWidget.currentRow()
        if(cR >= 0 and cR < len(ObjectsManager.images_list)):
            if(len(ObjectsManager.images_list) == 1):
                self.scene.RemoveActor(self.axial_slice)
                self.scene.RemoveActor(self.coronal_slice)
                self.scene.RemoveActor(self.sagittal_slice)
                self.axial_slice = 0
                self.coronal_slice = 0
                self.sagittal_slice = 0
                self.target_vs = 0
            ObjectsManager.RemoveImageObject(cR)
            self.volumesListWidget.takeItem(cR)
            self.volumesListWidget.setCurrentRow(0)
        
    def _file_clicked(self, _button):
        print('Clicked')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);Python Files (*.py)", options=options)
        if fileName:
            print(fileName)
            Q = fileName[len(fileName)-4:len(fileName)]
            if(Q == '.mat' or Q == '.MAT'):
                self.LoadAndDisplayTract(fileName,colorby='fe_seg')
            # A = self.mymenu.get_file_names()
        # SEL = self.mymenu.current_directory + '/' + self.mymenu.listbox.selected[0];
        
        
    def _load_volume_clicked(self,_button):
        print('Load volume')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);Python Files (*.py)", options=options)
        if fileName:
            print(fileName)
            Q = fileName[len(fileName)-4:len(fileName)]
            if(Q == '.nii' or Q == 'i.gz'):
                self.LoadAndDisplayImage(fileName)

    def _axial_slider_moved(self,_slider):
        z = self.axialSlider.value()-1
        z = int(z)
        if(self.axial_slice != 0):
            self.axial_slice.display_extent(0, self.axial_slice.shape[0] - 1, 0, self.axial_slice.shape[1] - 1, z, z)
            self.axial_slice.Modified()
            
        if(len(ObjectsManager.fod_list) > 0):
            args=(z,self.fod_subsamp)
            # self.fod_list[0].displayAxialFODs(z,subsamp_fac=8)
            # MethodInBackground(ObjectsManager.fod_list[0].displayAxialFODs,args)
            ObjectsManager.fod_list[0].displayAxialFODs(z,self.fod_subsamp)
            ObjectsManager.fod_list[0].Modified()
            
        self.axialEdit.setText(str(z))    
        self.iren.Render()     
                                    
    def _coronal_slider_moved(self,_slider):
        x = self.coronalSlider.value()-1
        x = int(x)
        if(self.coronal_slice != 0):
            self.coronal_slice.display_extent(0, self.coronal_slice.shape[0] - 1, x, x, 0, self.coronal_slice.shape[2]-1)
            self.coronal_slice.Modified()
        self.coronalEdit.setText(str(x))    
        self.iren.Render()     
                
    def _sagittal_slider_moved(self,_slider):
        x = self.sagittalSlider.value()-1
        x = int(x)
        if(self.sagittal_slice != 0):
            self.sagittal_slice.display_extent(x, x, 0, self.sagittal_slice.shape[1] - 1, 0, self.sagittal_slice.shape[2]-1)
            self.sagittal_slice.Modified()
        self.sagittalEdit.setText(str(x))    
        self.iren.Render()    
        
    def _axial_slider_edit(self):
        val = int(self.axialEdit.text())
        self.axialSlider.setValue(val)
            
    def _transparency_slider_moved(self,_slider):
        # print('_transparency_slider_moved')
        if(self.show_axial_plane == True and self.axial_slice != 0):
            self.axial_slice.opacity(self.volTransparencySlider.value()/255)
            self.axial_slice.Modified()
        if(self.show_sagittal_plane == True and self.sagittal_slice != 0):
            self.sagittal_slice.opacity(self.volTransparencySlider.value()/255)
            self.sagittal_slice.Modified()
        if(self.show_coronal_plane == True and self.coronal_slice != 0):
            self.coronal_slice.opacity(self.volTransparencySlider.value()/255)
            self.coronal_slice.Modified()
            
        ObjectsManager.images_list[self.current_image].alpha = self.volTransparencySlider.value()
        self.iren.Render()
    
    def _intensity_slider_moved(self,_slider):
        if(self.axial_slice != 0):
            ObjectsManager.images_list[self.current_image].minVal = self.volMinValSlider.value()
            ObjectsManager.images_list[self.current_image].maxVal = self.volMaxValSlider.value()
            self.UpdateImageSlice(which_image=self.current_image,minclip=self.volMinValSlider.value(),
                                              maxclip=self.volMaxValSlider.value())
            self.volMinValEdit.setText(str(self.volMinValSlider.value()/255))
            self.volMaxValEdit.setText(str(self.volMaxValSlider.value()/255))
            # self.axial_slice.Modified()
            self.iren.Render()
    
    def _intensity_edit(self):
            self.volMinValSlider.setValue(int(self.volMinValEdit.text()))
            self.volMaxValSlider.setValue(int(self.volMaxValEdit.text()))
    
    def _volColormapSelected(self,theNewVal):
        if(self.current_image < len(ObjectsManager.images_list)):
            ObjectsManager.images_list[self.current_image].colormap = self.available_colormaps[theNewVal]
            self.UpdateImageSlice(which_image=self.current_image)            
    
    def _fod_subsamp_slider_moved(self,_slider):
        self.fod_subsamp = int(self.fodSubsampSlider.value())
    
    def _highlight_checkbox_state_changed(self,_checkbox):            
        print('_checkbox_state_changed')
        if(self.highlightedOnlyCheckbox.isChecked()):
            for actor in ObjectsManager.tracts_list:
                actor.GetProperty().SetOpacity(0.2)
                actor.Modified()
        else:
            for actor in ObjectsManager.tracts_list:
                actor.GetProperty().SetOpacity(1.0)
                actor.Modified()
        self.iren.Render()
        
    def _axialimage_checkbox_state_changed(self,_checkbox):
        if(self.axialImageCheckBox.isChecked()):
            self.show_axial_plane = True
        else:
            self.show_axial_plane = False
        self.UpdateImageSlice(which_image=self.current_image)
        
    def _coronalimage_checkbox_state_changed(self,_checkbox):
        if(self.coronalImageCheckBox.isChecked()):
            self.show_coronal_plane = True
        else:
            self.show_coronal_plane = False
        self.UpdateImageSlice(which_image=self.current_image)

    def _sagittalimage_checkbox_state_changed(self,_checkbox):
        if(self.sagittalImageCheckBox.isChecked()):
            self.show_sagittal_plane = True
        else:
            self.show_sagittal_plane = False
        self.UpdateImageSlice(which_image=self.current_image)
                        
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

    def _delete_FOD_button(self,_button):
        if(len(ObjectsManager.fod_list) > 0):
            self.scene.RemoveActor(ObjectsManager.fod_list[0])            
            ObjectsManager.RemoveFODObject()
                        
    def _delete_ROI_button(self,_button):
        if(len(ObjectsManager.rois_list) > 0):
            self.scene.RemoveActor(ObjectsManager.rois_list[self.troiListWidget.currentRow()].actor)            
            ObjectsManager.RemoveROIObject(self.troiListWidget.currentRow())

    def _toggle_ROI_button(self,_button):
        ObjectsManager.rois_list[self.roiListWidget.currentRow()].enabled = not ObjectsManager.rois_list[self.roiListWidget.currentRow()].enabled
        for tract in ObjectsManager.tracts_list:
            tract.color_tracts_by_roi_intersection_optimized(
                rois_list = ObjectsManager.rois_list,
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
                        
            for tract in ObjectsManager.tracts_list:
                tract.color_tracts_by_roi_intersection_optimized(
                    rois_list = ObjectsManager.rois_list,
                    #intersect_color = (1,0,0),
                    alpha_outside = 0.3
                )
            self.iren.Render()
        
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
                print('Found tract in list ' + str(index))
                self.tractsListWidget.setCurrentRow(index)
                self.current_actor_properties = vtk.vtkProperty()
                self.current_actor_properties.DeepCopy(self.current_actor.GetProperty())
                ObjectsManager.tracts_list[index].ActorHighlightedProps()
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
            self._interactor_camera() # empty click -> default camera behavior

        # except:
            # print('Nothing to do')
        self.style.OnLeftButtonDown()
        
        # self.iren.Render()
        
    def LoadAndDisplayImage(self, filename, minclip=0,maxclip=255):
        fparts = filename.split("/")
        if(len(ObjectsManager.images_list) == 0):
            tvs = 0
        else:
            tvs = self.target_vs
            
        new_image = ImageObject(filename, fparts[-1], target_vs=tvs, minVal=0, maxVal=255, alpha=255, colormap='gray')
        if(type(tvs) == int or type(tvs) == float):
            self.target_vs = np.diag(new_image.affine)
        
        print('LoadAndDisplayImage')
        print(new_image.affine)
        
        ObjectsManager.AddImageObject(new_image)

        self.volTransparencySlider.setMinimum(0)
        self.volTransparencySlider.setMaximum(255)
        self.volTransparencySlider.setValue(255)

        dataV = new_image.data

        z = int(np.round(dataV.shape[2]/2))
        self.axialSlider.setMinimum(1)
        self.axialSlider.setMaximum(dataV.shape[2])
        self.axialSlider.setValue(z+1)

        x = int(np.round(dataV.shape[1]/2))
        self.coronalSlider.setMinimum(1)
        self.coronalSlider.setMaximum(dataV.shape[1])
        self.coronalSlider.setValue(x+1)

        y = int(np.round(dataV.shape[0]/2))
        self.sagittalSlider.setMinimum(1)
        self.sagittalSlider.setMaximum(dataV.shape[0])
        self.sagittalSlider.setValue(y+1)
        
        minV = int(dataV.min()*255)
        maxV = int(dataV.max()*255)
        self.volMinValSlider.setMinimum(minV)
        self.volMinValSlider.setMaximum(maxV)
        self.volMinValSlider.setValue(minV)

        self.volMaxValSlider.setMinimum(minV)
        self.volMaxValSlider.setMaximum(maxV)
        self.volMaxValSlider.setValue(maxV)        

        self.volMinValEdit.setText(str(minV/255))
        self.volMaxValEdit.setText(str(maxV/255))

        self.volumesListWidget.addItem(fparts[-1])
        self.current_image = len(ObjectsManager.images_list)-1
        self.volumesListWidget.setCurrentRow(self.current_image)
        self.UpdateImageSlice(which_image=self.current_image)

    def UpdateImageSlice(self, which_image=0, minclip=0,maxclip=255):   
        print('UpdateImageSlice ' + str(which_image))
        if(self.axial_slice != 0):
            self.scene.RemoveActor(self.axial_slice)
        if(self.coronal_slice != 0):
            self.scene.RemoveActor(self.coronal_slice)
        if(self.sagittal_slice != 0):
            self.scene.RemoveActor(self.sagittal_slice)
            
        ObjectsManager.images_list[which_image].UpdateMinMax(minclip=self.volMinValSlider.value(),
            maxclip=self.volMaxValSlider.value())    
        ObjectsManager.images_list[which_image].UpdateLUT()    
        
        dataV = ObjectsManager.images_list[which_image].data
        data_aff = ObjectsManager.images_list[which_image].affine        
        minV = ObjectsManager.images_list[which_image].minVal
        maxV = ObjectsManager.images_list[which_image].maxVal
        lut = ObjectsManager.images_list[which_image].lut
        
        if(self.show_axial_plane == True):
            z = self.axialSlider.value()-1
            self.axial_slice = actor.slicer(dataV,affine=data_aff,value_range=(minV,maxV),lookup_colormap=lut)
            self.scene.AddActor(self.axial_slice)
            self.axial_slice.display_extent(0, dataV.shape[0] - 1, 0, dataV.shape[1] - 1, z, z)
        if(self.show_coronal_plane == True):
            x = self.coronalSlider.value()-1
            self.coronal_slice = actor.slicer(dataV,affine=data_aff,value_range=(minV,maxV),lookup_colormap=lut)
            self.coronal_slice.display_extent(0, dataV.shape[1] - 1, x, x, 0, dataV.shape[2]-1)
            self.scene.AddActor(self.coronal_slice)
        if(self.show_sagittal_plane == True):
            y = self.sagittalSlider.value()-1
            self.sagittal_slice = actor.slicer(dataV,affine=data_aff,value_range=(minV,maxV),lookup_colormap=lut)
            self.scene.AddActor(self.sagittal_slice)
            self.sagittal_slice.display_extent(y, y, 0, dataV.shape[0] - 1, 0, dataV.shape[2]-1)

        #self.scene.ResetCamera()
        self.scene.ResetCameraClippingRange()
        self.iren.Render()
       
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
        

    def LoadAndDisplayTract(self,filename,colorby='fe_seg'):
        print('Going to load ' + filename)
        
        #ObjectsManager.images_list[self.current_image]
        if('.trk' in filename or '.vtk' in filename):
            if(self.current_image < len(ObjectsManager.images_list)):
                tractography = TractographyObject(filename,colorby,affine=ObjectsManager.images_list[self.current_image].affine,size4centering=ObjectsManager.images_list[self.current_image].data.shape)
            else:
                print('First load and select a reference image')
                return
        else:
            tractography = TractographyObject(filename,colorby,affine=ObjectsManager.images_list[self.current_image].affine)

        ObjectsManager.AddTractographyObject(tractography)
        
        self.scene.AddActor(tractography.actor)
        self.scene.ResetCamera()
        self.scene.ResetCameraClippingRange()
        
        filename = filename.replace('\\','/')
        filename = filename.split('/')       
                            
        self.tractsListWidget.addItem(filename[-1])

        self.iren.Render()
        print('Done')

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
                self.LoadAndDisplayImage(f)
            elif('.mat' in f or '.trk' in f or '.tck' in f or '.vtk' in f):
                self.LoadAndDisplayTract(f)
                
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
