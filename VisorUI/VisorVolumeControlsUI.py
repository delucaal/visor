#!/usr/bin/env python3

import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QApplication

from fury import actor,colormap

from VisorUtils.ObjectsManagement import ObjectsManager
from VisorUtils.VisorObjects import ROIObject, ImageObject, TractographyObject

class VisorVolumeControlsUI(object):
    available_colormaps = ('gray','viridis','plasma','inferno')
    current_image = 0
    show_axial_plane = True
    show_coronal_plane = True
    show_sagittal_plane = True
    shared = None

    def __init__(self, parent):
        self.mainapp = parent
        VisorVolumeControlsUI.shared = self
        
        self.axial_slice = 0
        self.coronal_slice = 0
        self.sagittal_slice = 0
        self.target_vs = 0
        
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

    def _link_qt_actions(self):
        self.loadVolumeButton.clicked.connect(self._load_volume_clicked)
        self.unloadVolButton.clicked.connect(self._unload_volume_clicked)
        self.volumesListWidget.itemClicked.connect(self._volume_clicked)

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
        
        self.axialImageCheckBox.stateChanged.connect(self._axialimage_checkbox_state_changed)
        self.coronalImageCheckBox.stateChanged.connect(self._coronalimage_checkbox_state_changed)
        self.sagittalImageCheckBox.stateChanged.connect(self._sagittalimage_checkbox_state_changed)
        self.highlightedOnlyCheckbox.stateChanged.connect(self._highlight_checkbox_state_changed)
            
    def _load_volume_clicked(self,_button):
        print('Load volume')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self.mainapp,"QFileDialog.getOpenFileName()", "","All Files (*)", options=options)
        if fileName:
            print(fileName)
            Q = fileName[len(fileName)-4:len(fileName)]
            if(Q == '.nii' or Q == '.nii.gz'):
                self.LoadAndDisplayImage(fileName)        
                
    def _unload_volume_clicked(self,_item):
        cR = self.volumesListWidget.currentRow()
        if(cR >= 0 and cR < len(ObjectsManager.images_list)):
            if(len(ObjectsManager.images_list) == 1):
                #self.axial_slice.RemoveActorFromScene()
                #self.coronal_slice.RemoveActorFromScene()
                #self.sagittal_slice.RemoveActorFromScene()
                self.mainapp.scene.RemoveActor(self.axial_slice)
                self.mainapp.scene.RemoveActor(self.coronal_slice)
                self.mainapp.scene.RemoveActor(self.sagittal_slice)
                self.axial_slice = 0
                self.coronal_slice = 0
                self.sagittal_slice = 0
                self.target_vs = 0
            ObjectsManager.RemoveImageObject(cR)
            self.volumesListWidget.takeItem(cR)
            self.volumesListWidget.setCurrentRow(0)      
            
    ## Volume related actions
    def _volume_clicked(self,_item):
        cR = self.volumesListWidget.currentRow()
        print('volume_clicked ' + str(cR))
        previous_image = VisorVolumeControlsUI.current_image
        VisorVolumeControlsUI.current_image = cR
        self.volMinValSlider.setValue(ObjectsManager.images_list[VisorVolumeControlsUI.current_image].minVal)
        self.volMaxValSlider.setValue(ObjectsManager.images_list[VisorVolumeControlsUI.current_image].maxVal)
        self.volTransparencySlider.setValue(ObjectsManager.images_list[VisorVolumeControlsUI.current_image].alpha)
        self.volColormapBox.setCurrentIndex(self.available_colormaps.index(ObjectsManager.images_list[VisorVolumeControlsUI.current_image].colormap))
        self.UpdateImageSliders(which_image=VisorVolumeControlsUI.current_image,previous_image=previous_image)
        self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image)
        
    def _axial_slider_moved(self,_slider):
        if(VisorVolumeControlsUI.current_image > len(ObjectsManager.images_list)-1):
            return
        back_projection = ObjectsManager.images_list[VisorVolumeControlsUI.current_image].InvertAffineFromPointWC([self.sagittalSlider.value(),
                            self.coronalSlider.value(),self.axialSlider.value()])
        z = int(back_projection[2])
        self.UpdateImageSliceAxial(z)
            
        if(len(ObjectsManager.fod_list) > 0):
            args=(z,self.mainapp.fod_subsamp)
            # self.fod_list[0].displayAxialFODs(z,subsamp_fac=8)
            # MethodInBackground(ObjectsManager.fod_list[0].displayAxialFODs,args)
            ObjectsManager.fod_list[0].displayAxialFODs(z,self.mainapp.fod_subsamp)
            ObjectsManager.fod_list[0].Modified()
            
        self.axialEdit.setText(str(self.axialSlider.value()))   
        self.mainapp.iren.Render()            
        
    def _coronal_slider_moved(self,_slider):
        if(VisorVolumeControlsUI.current_image > len(ObjectsManager.images_list)-1):
            return
        back_projection = ObjectsManager.images_list[VisorVolumeControlsUI.current_image].InvertAffineFromPointWC([self.sagittalSlider.value(),
                            self.coronalSlider.value(),self.axialSlider.value()])
        x = int(back_projection[1])
        self.coronalEdit.setText(str(self.coronalSlider.value()))    
        self.UpdateImageSliceCoronal(x)
        self.mainapp.iren.Render()     
                
    def _sagittal_slider_moved(self,_slider):
        if(VisorVolumeControlsUI.current_image > len(ObjectsManager.images_list)-1):
            return
        back_projection = ObjectsManager.images_list[VisorVolumeControlsUI.current_image].InvertAffineFromPointWC([self.sagittalSlider.value(),
                            self.coronalSlider.value(),self.axialSlider.value()])
        x = int(back_projection[0])
        self.UpdateImageSliceSagittal(x)
        self.sagittalEdit.setText(str(self.sagittalSlider.value()))#x))    
        self.iren.Render()            
        
    def _sagittal_slider_moved(self,_slider):
        if(VisorVolumeControlsUI.current_image > len(ObjectsManager.images_list)-1):
            return
        back_projection = ObjectsManager.images_list[VisorVolumeControlsUI.current_image].InvertAffineFromPointWC([self.sagittalSlider.value(),
                            self.coronalSlider.value(),self.axialSlider.value()])
        x = int(back_projection[0])
        self.UpdateImageSliceSagittal(x)
        self.sagittalEdit.setText(str(self.sagittalSlider.value()))#x))    
        self.mainapp.iren.Render()    
        
    def _axial_slider_edit(self):
        val = int(self.axialEdit.text())
        self.axialSlider.setValue(val)
            
    def _transparency_slider_moved(self,_slider):
        if(VisorVolumeControlsUI.current_image > len(ObjectsManager.images_list)-1):
            return
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
            
        ObjectsManager.images_list[VisorVolumeControlsUI.current_image].alpha = self.volTransparencySlider.value()
        self.mainapp.iren.Render()
    
    def _intensity_slider_moved(self,_slider):
        if(self.axial_slice != 0):
            ObjectsManager.images_list[VisorVolumeControlsUI.current_image].minVal = self.volMinValSlider.value()
            ObjectsManager.images_list[VisorVolumeControlsUI.current_image].maxVal = self.volMaxValSlider.value()
            self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image,minclip=self.volMinValSlider.value(),
                                              maxclip=self.volMaxValSlider.value())
            self.volMinValEdit.setText(str(self.volMinValSlider.value()/255))
            self.volMaxValEdit.setText(str(self.volMaxValSlider.value()/255))
            self.mainapp.iren.Render()
    
    def _intensity_edit(self):
            self.volMinValSlider.setValue(int(self.volMinValEdit.text()))
            self.volMaxValSlider.setValue(int(self.volMaxValEdit.text()))
    
    def _volColormapSelected(self,theNewVal):
        if(VisorVolumeControlsUI.current_image < len(ObjectsManager.images_list)):
            ObjectsManager.images_list[VisorVolumeControlsUI.current_image].colormap = self.available_colormaps[theNewVal]
            self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image)            
    
    def _axialimage_checkbox_state_changed(self,_checkbox):
        if(self.axialImageCheckBox.isChecked()):
            self.show_axial_plane = True
        else:
            self.show_axial_plane = False
        self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image)
        
    def _coronalimage_checkbox_state_changed(self,_checkbox):
        if(self.coronalImageCheckBox.isChecked()):
            self.show_coronal_plane = True
        else:
            self.show_coronal_plane = False
        self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image)

    def _sagittalimage_checkbox_state_changed(self,_checkbox):
        if(self.sagittalImageCheckBox.isChecked()):
            self.show_sagittal_plane = True
        else:
            self.show_sagittal_plane = False
        self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image)        
        
    def _highlight_checkbox_state_changed(self,_checkbox):            
        if(self.highlightedOnlyCheckbox.isChecked()):
            for tract in ObjectsManager.tracts_list:
                tract.actor.GetProperty().SetOpacity(0.2)
                tract.actor.Modified()
        else:
            for tract in ObjectsManager.tracts_list:
                tract.actor.GetProperty().SetOpacity(1.0)
                tract.actor.Modified()
        self.mainapp.iren.Render()
        
    def UpdateImageSliceAxial(self,z):
            if(self.axial_slice != 0 and z >= 0 and z < self.axial_slice.shape[2]):
                self.axial_slice.display_extent(0, self.axial_slice.shape[0] - 1, 0, self.axial_slice.shape[1] - 1, z, z)
                self.axial_slice.Modified()
            else:
                print('Axial slice not available')
    
    def UpdateImageSliceCoronal(self,x):             
        if(self.coronal_slice != 0 and x >= 0 and x < self.coronal_slice.shape[1]):
            self.coronal_slice.display_extent(0, self.coronal_slice.shape[0] - 1, x, x, 0, self.coronal_slice.shape[2]-1)
            self.coronal_slice.Modified()
        else:
            print('Coronal slice not available')
           
    def UpdateImageSliceSagittal(self,y):
        if(self.sagittal_slice != 0 and y >= 0 and y < self.sagittal_slice.shape[0]):
            self.sagittal_slice.display_extent(y, y, 0, self.sagittal_slice.shape[1] - 1, 0, self.sagittal_slice.shape[2]-1)
            self.sagittal_slice.Modified()
        else:
            print('Sagittal slice not available')

    def UpdateImageSlice(self, which_image=0, minclip=0,maxclip=255):   
        print('UpdateImageSlice ' + str(which_image))
        if(self.axial_slice != 0):
            self.mainapp.scene.RemoveActor(self.axial_slice)
        if(self.coronal_slice != 0):
            self.mainapp.scene.RemoveActor(self.coronal_slice)
        if(self.sagittal_slice != 0):
            self.mainapp.scene.RemoveActor(self.sagittal_slice)
            
        ObjectsManager.images_list[which_image].UpdateMinMax(minclip=self.volMinValSlider.value(),
            maxclip=self.volMaxValSlider.value())    
        ObjectsManager.images_list[which_image].UpdateLUT()    
        
        dataV = ObjectsManager.images_list[which_image].data
        data_aff = ObjectsManager.images_list[which_image].affine        
        minV = ObjectsManager.images_list[which_image].minVal
        maxV = ObjectsManager.images_list[which_image].maxVal
        lut = ObjectsManager.images_list[which_image].lut
        
        #extents = ObjectsManager.images_list[which_image].max_extent # np.abs(np.matmul(data_aff[0:3,0:3],dataV.shape)).astype(int)
        back_projection = ObjectsManager.images_list[which_image].InvertAffineFromPointWC([self.sagittalSlider.value(),
                            self.coronalSlider.value(),self.axialSlider.value()])
        
        if(self.show_axial_plane == True):
            self.axial_slice = actor.slicer(dataV,affine=data_aff,value_range=(minV,maxV),lookup_colormap=lut)
            self.mainapp.scene.AddActor(self.axial_slice)
            #self.axial_slice.AddActorToScene(self.mainapp.scene)
            z = int(back_projection[2])
            self.UpdateImageSliceAxial(z)

        if(self.show_coronal_plane == True):
            self.coronal_slice = actor.slicer(dataV,affine=data_aff,value_range=(minV,maxV),lookup_colormap=lut)
            self.mainapp.scene.AddActor(self.coronal_slice)
            #self.coronal_slice.AddActorToScene(self.mainapp.scene)
            x = int(back_projection[1])
            self.UpdateImageSliceCoronal(x)
            
        if(self.show_sagittal_plane == True):
            self.sagittal_slice = actor.slicer(dataV,affine=data_aff,value_range=(minV,maxV),lookup_colormap=lut)
            self.mainapp.scene.AddActor(self.sagittal_slice)
            #self.sagittal_slice.AddActorToScene(self.mainapp.scene)
            y = int(back_projection[0])
            self.UpdateImageSliceSagittal(y)

        #self.scene.ResetCamera()
        self.mainapp.scene.ResetCameraClippingRange()
        self.mainapp.iren.Render()

    def UpdateImageSliders(self,which_image=0,previous_image=0):
        new_image = ObjectsManager.images_list[which_image]
        #old_image = ObjectsManager.images_list[previous_image]
        dataV = new_image.data
        
        rmin_extent = new_image.min_extent
        rmax_extent = new_image.max_extent

        axval = self.axialSlider.value()
        corval = self.coronalSlider.value()
        sagval = self.sagittalSlider.value()
            
        if(previous_image != which_image):
            print('Updating image sliders for image ' + str(which_image))
            p = np.asarray([sagval,corval,axval])
            #p_transformed = old_image.InvertAffineFromPointWC(p)
            #p_back = new_image.ApplyAffineToPointWC(p_transformed)
            p_back = p 
            sagval = int(p_back[0])
            corval = int(p_back[1])
            axval = int(p_back[2])
        
        #z = int(np.round(dataV.shape[2]/2))
        #cval = self.axialSlider.value()
        self.axialSlider.setMinimum(rmin_extent[2])
        self.axialSlider.setMaximum(rmax_extent[2])
        if(axval < rmin_extent[2] or axval > rmax_extent[2]):
            self.axialSlider.setValue(int((rmin_extent[2]+rmax_extent[2])/2)+1)
        else:
            self.axialSlider.setValue(axval)

        #x = int(np.round(dataV.shape[1]/2))
        self.coronalSlider.setMinimum(rmin_extent[1])
        #self.coronalSlider.setMaximum(dataV.shape[1])
        self.coronalSlider.setMaximum(rmax_extent[1])
        if(corval < rmin_extent[1] or corval > rmax_extent[1]):
            self.coronalSlider.setValue(int((rmin_extent[1]+rmax_extent[1])/2)+1)
        else:
            self.coronalSlider.setValue(corval)

        #y = int(np.round(dataV.shape[0]/2))
        self.sagittalSlider.setMinimum(rmin_extent[0])
        #self.sagittalSlider.setMaximum(dataV.shape[0])
        self.sagittalSlider.setMaximum(rmax_extent[0])
        if(sagval < rmin_extent[0] or sagval > rmax_extent[0]):
            self.sagittalSlider.setValue(int((rmin_extent[0]+rmax_extent[0])/2)+1)
        else:
            self.sagittalSlider.setValue(sagval)
        
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

        self.volumesListWidget.addItem(fparts[-1])
        VisorVolumeControlsUI.current_image = len(ObjectsManager.images_list)-1
        self.volumesListWidget.setCurrentRow(VisorVolumeControlsUI.current_image)
        self.UpdateImageSliders(which_image=VisorVolumeControlsUI.current_image)
        self.UpdateImageSlice(which_image=VisorVolumeControlsUI.current_image)          
            