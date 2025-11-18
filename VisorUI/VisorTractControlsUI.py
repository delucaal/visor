#!/usr/bin/env python3

import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QApplication

import vtk
from fury import actor,colormap
import os

from VisorUtils.ObjectsManagement import ObjectsManager
from VisorUtils.VisorObjects import ROIObject, ImageObject, TractographyObject
from VisorUI.VisorVolumeControlsUI import VisorVolumeControlsUI

class VisorTractControlsUI(object):
    def __init__(self, parent):
        self.mainapp = parent
        
        self.loadSingleTractButton = parent.findChild(QtWidgets.QPushButton,'loadSingleTract')
        self.loadAllTractsButton = parent.findChild(QtWidgets.QPushButton,'loadAllTracts')
        self.deleteAllTractsButton = parent.findChild(QtWidgets.QPushButton,'deleteAllTracts')
        self.deleteOneTractButton = parent.findChild(QtWidgets.QPushButton,'deleteOneTractButton')
        self.toggleClipButton = parent.findChild(QtWidgets.QPushButton,'toggleClipButton')

        self.tractsSubsamplingSlider = parent.findChild(QtWidgets.QSlider,'subsamplingSlider')        
        self.tractColRedSlider = parent.findChild(QtWidgets.QSlider,'tractColRedSlider')
        self.tractColGreenSlider = parent.findChild(QtWidgets.QSlider,'tractColGreenSlider')
        self.tractColBlueSlider = parent.findChild(QtWidgets.QSlider,'tractColBlueSlider')
        self.tractColAlphaSlider = parent.findChild(QtWidgets.QSlider,'tractColAlphaSlider')
        self.tractThickSlider = parent.findChild(QtWidgets.QSlider,'tractThickSlider')
        self.tractColDECButton = parent.findChild(QtWidgets.QPushButton,'tractColDECButton')
        self.hideShowAllTractsButton = parent.findChild(QtWidgets.QPushButton,'hideShowAllTractsButton')        
        self.clipThickSlider = parent.findChild(QtWidgets.QSlider,'clipThickSlider')
        self.zClipSlider = parent.findChild(QtWidgets.QSlider,'zClipSlider')
        self.yClipSlider = parent.findChild(QtWidgets.QSlider,'yClipSlider')
        self.xClipSlider = parent.findChild(QtWidgets.QSlider,'xClipSlider')
        
        self.tractsListWidget = parent.findChild(QtWidgets.QListWidget,'tractsList')
        
        
    def _link_qt_actions(self):
        self.loadSingleTractButton.clicked.connect(self._file_clicked)
        self.loadAllTractsButton.clicked.connect(self._all_files_clicked)
        self.deleteAllTractsButton.clicked.connect(self._delete_all_tracts)
        self.deleteOneTractButton.clicked.connect(self._delete_one_tract)
        self.tractColDECButton.clicked.connect(self._tract_color_dec)
        self.hideShowAllTractsButton.clicked.connect(self._hide_show_all_tracts_button)
        self.toggleClipButton.clicked.connect(self._clip_toggle_button)
        
        self.tractColRedSlider.valueChanged.connect(self._tract_color_slider_changed)
        self.tractColGreenSlider.valueChanged.connect(self._tract_color_slider_changed)
        self.tractColBlueSlider.valueChanged.connect(self._tract_color_slider_changed)
        self.tractColAlphaSlider.valueChanged.connect(self._tract_thick_slider_changed)
        self.tractThickSlider.valueChanged.connect(self._tract_thick_slider_changed)
        self.clipThickSlider.valueChanged.connect(self._clip_thickness_slider_moved)
        self.zClipSlider.valueChanged.connect(self._z_clip_slider_moved)
        self.yClipSlider.valueChanged.connect(self._y_clip_slider_moved)
        self.xClipSlider.valueChanged.connect(self._x_clip_slider_moved)

        self.tractsListWidget.itemClicked.connect(self._track_clicked)
        
        self.tractsSubsamplingSlider.valueChanged.connect(self._tracts_subsampling_slider_moved)

    ## Tract related actions    
    def _track_clicked(self, _item):
        cR = self.tractsListWidget.currentRow()
        self.mainapp.current_actor = ObjectsManager.tracts_list[cR].actor
        self.mainapp.current_actor_properties = vtk.vtkProperty()
        self.mainapp.current_actor_properties.DeepCopy(self.mainapp.current_actor.GetProperty())
        self.mainapp.current_actor.GetProperty().SetOpacity(1.0)
        self.mainapp.iren.Render()

        print('_track_clicked ' + str(cR))
        #self.tractPropertiesContainer.setVisible(True)
        
        # Ensure tracts are only inspected and not moved
        self.mainapp._interactor_camera()

    def _hide_show_all_tracts_button(self,_button):
        print('Hide/show all tracts')
        for tract in ObjectsManager.tracts_list:
            if(tract.actor.GetVisibility() == 1):
                tract.actor.VisibilityOff()
            else:
                tract.actor.VisibilityOn()
    
        self.mainapp.iren.Render()

    def _clip_toggle_button(self,_button):
        print('Clip toggle button')
        #affine = ObjectsManager.images_list[self.current_image].affine
        #coords = np.asarray([self.coronalSlider.value(),self.sagittalSlider.value(),self.axialSlider.value(),1])
        for tract in ObjectsManager.tracts_list:
            tract.ClipDisable()
            #tract.ClipTractsByCoordinatesWithShaders(current_slice_pos = self.axialSlider.value(), current_axis = 2, current_slice_thickness = 0.1)    
        self.mainapp.iren.Render()
        
    def LoadAndDisplayTract(self,filename,colorby='fe_seg'):
        print('Going to load ' + filename)
        
        current_image = VisorVolumeControlsUI.current_image
        #ObjectsManager.images_list[self.current_image]
        if(len(ObjectsManager.images_list) < 1 or current_image < 0):
            print('You should first load and select a reference image')
            affine = np.eye(4)
        else:
            affine = ObjectsManager.images_list[current_image].affine
        if('.trk' in filename or '.vtk' in filename):
            if(current_image < len(ObjectsManager.images_list)):
                tractography = TractographyObject(filename,colorby,affine=affine,size4centering=ObjectsManager.images_list[current_image].data.shape)
            else:
                print('First load and select a reference image')
                return
        else:
            tractography = TractographyObject(filename,colorby,affine=affine)

        ObjectsManager.AddTractographyObject(tractography)
        
        self.mainapp.scene.AddActor(tractography.actor)
        if(len(ObjectsManager.tracts_list) == 1):
            self.mainapp.scene.ResetCamera()
        self.mainapp.scene.ResetCameraClippingRange()
        
        filename = filename.replace('\\','/')
        filename = filename.split('/')       
                            
        self.tractsListWidget.addItem(filename[-1])
        self.mainapp.ROIsTreeWidget.addTopLevelItem(QtWidgets.QTreeWidgetItem([filename[-1]]))

        self.mainapp.iren.Render()
        print('Done')
        
    def _file_clicked(self, _button):
        print('Clicked')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self.mainapp,"QFileDialog.getOpenFileName()", "","All Files (*);Python Files (*.py)", options=options)
        if fileName:
            print(fileName)
            Q = fileName[len(fileName)-4:len(fileName)]
            if(Q == '.mat' or Q == '.MAT'):
                self.LoadAndDisplayTract(fileName,colorby='fe_seg')
            # A = self.mymenu.get_file_names()
        # SEL = self.mymenu.current_directory + '/' + self.mymenu.listbox.selected[0];            
                
    def _all_files_clicked(self, _button):
        print('Load all')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        the_dir = QFileDialog.getExistingDirectory(self.mainapp,"QFileDialog.getOpenFileName()", options=options)
        if(len(the_dir) < 1):
            return
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
            self.mainapp.scene.RemoveActor(actor.actor)
            
        ObjectsManager.RemoveTractographyObjects()
        self.tractsListWidget.clear()
        self.mainapp.scene.ResetCamera()
        self.mainapp.scene.ResetCameraClippingRange()
        
    def _delete_one_tract(self,_button):
        print('delete one tract')
        sel_items = self.tractsListWidget.selectedItems()        
        tracts_2_delete = []
        for item in sel_items:
            row = self.tractsListWidget.row(item)          
            tracts_2_delete.append(row)
        for zin in range(len(tracts_2_delete)-1,-1,-1):
            self.tractsListWidget.takeItem(tracts_2_delete[zin])
            self.mainapp.scene.RemoveActor(ObjectsManager.tracts_list[zin].actor)
            ObjectsManager.RemoveTractographyObject(zin)
            
        self.mainapp.iren.Render()
                
    def _tract_color_dec(self,_button):
        print('_tract_color_dec')
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]
        cR.SetColorDEC()
        cR.actor.Modified()
        self.mainapp.iren.Render()

    def _tract_thick_slider_changed(self,_item):
        # if(self.current_actor != 0):
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]    
        cR.actor.GetProperty().SetLineWidth(self.tractThickSlider.value())
        cR.actor.GetProperty().SetOpacity(float(self.tractColAlphaSlider.value())/255.0)
        if(self.mainapp.current_actor_properties != 0):
            self.mainapp.current_actor_properties.DeepCopy(cR.actor.GetProperty())
        cR.actor.Modified()
        self.mainapp.iren.Render()
        
    def _clip_thickness_slider_moved(self,_item):
        print('_clip_thickness_slider_moved ' + str(self.clipThickSlider.value()))
        for tract in ObjectsManager.tracts_list:
            tract.ClipTractsByCoordinatesWithShaders(current_slice_thickness=self.clipThickSlider.value()/1e2)
        self.mainapp.iren.Render()
        
    def _z_clip_slider_moved(self,_item):
        print('_z_clip_slider_moved ' + str(self.zClipSlider.value()))
        for tract in ObjectsManager.tracts_list:
            tract.ClipTractsByCoordinatesWithShaders(current_slice_pos=self.zClipSlider.value()/1e2, current_axis=2, current_slice_thickness=self.clipThickSlider.value()/1e2)
        self.mainapp.iren.Render()
        
    def _y_clip_slider_moved(self,_item):
        print('_y_clip_slider_moved ' + str(self.yClipSlider.value()))
        for tract in ObjectsManager.tracts_list:
            tract.ClipTractsByCoordinatesWithShaders(current_slice_pos=self.yClipSlider.value()/1e2, current_axis=1, current_slice_thickness=self.clipThickSlider.value()/1e2)
        self.mainapp.iren.Render()
        
    def _x_clip_slider_moved(self,_item):
        print('_x_clip_slider_moved ' + str(self.xClipSlider.value()))
        for tract in ObjectsManager.tracts_list:
            tract.ClipTractsByCoordinatesWithShaders(current_slice_pos=self.xClipSlider.value()/1e2, current_axis=0, current_slice_thickness=self.clipThickSlider.value()/1e2)
        self.mainapp.iren.Render()
                
    def _tracts_subsampling_slider_moved(self,_item):
        #print('_tracts_subsampling_slider_moved ' + str(self.tractsSubsamplingSlider.value()))
        cR = self.tractsListWidget.currentRow()
        if(len(ObjectsManager.tracts_list) == 0 or cR > len(ObjectsManager.tracts_list)-1):
            return
        cR = ObjectsManager.tracts_list[cR]    
        factor = self.tractsSubsamplingSlider.value()
        if(factor < 1):
            factor = 1
        if(factor > 1):        
            cR.EnableUndersamplingWithFactor(factor)
        else:
            cR.DisableUndersampling()
        cR.actor.Modified()
        self.mainapp.iren.Render()           
        
    def _tract_color_slider_changed(self,_item):
        # if(self.current_actor != 0):
        print('_tract_color_slider_changed ' + str(self.tractColRedSlider.value()))
        cR = self.tractsListWidget.currentRow()
        cR = ObjectsManager.tracts_list[cR]
        cR.SetColorSingle(red=self.tractColRedSlider.value(),
                                                 green=self.tractColGreenSlider.value(),
                                                 blue=self.tractColBlueSlider.value())
        cR.actor.GetProperty().SetOpacity(float(self.tractColAlphaSlider.value())/255.0)
        if(self.mainapp.current_actor_properties != 0):
            self.mainapp.current_actor_properties.DeepCopy(cR.actor.GetProperty())
        cR.actor.Modified()
        self.mainapp.iren.Render()             