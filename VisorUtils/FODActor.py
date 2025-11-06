# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 08:21:55 2020

@author: Alberto De Luca (alberto.deluca.06@gmail.com)
"""

import nibabel as nib
from fury import window, actor, ui, utils

from dipy.data import get_sphere
import dipy.reconst.shm as shm

import vtk
import numpy as np

class visorFODActor(vtk.vtkActor):
    odf_data = 0
    master_actor = 0
    can_update_rendering = 1
        
    def __init__(self):
        super(visorFODActor,self).__init__()
        self.target_vs = [1,1,1]        
        self.my_vs = [1,1,1]
        
    def setTargetVoxelSize(self,voxelsize=[1,1,1]):
        self.target_vs = voxelsize
        
    def loadFile(self,filename):
        self.ReferenceFile = filename
        
        orig_data = nib.load(filename)

        self.odf_data = orig_data.get_fdata()
        self.my_vs = np.diag(orig_data.affine)
        self.target_vs = self.my_vs
        self.origin = orig_data.affine[0:3,3]
        
        self.sphere = get_sphere('symmetric362')
        self.scale = np.array([1, 1, 1])
        #self.scale = np.diag(orig_data.affine)
        
    def setZValue(self,the_slice):
        self.which_slice = the_slice

    def setRenderer(self,the_renderer):
        self.renderer = the_renderer

    def displayAxialFODs(self,which_slice,subsamp_fac=2):
        print('displayAxialFODs ' + str(which_slice))
        # if(self.can_update_rendering == 0):
        #     print('Already busy rendering')
        #     return
        self.can_update_rendering = 0
        if(type(which_slice) is tuple):
            subsamp_fac = 1#which_slice[1]
            which_slice = which_slice[0]
            print('Unpacking tuples: subsamp is ' + str(subsamp_fac) + ' in slice ' + str(which_slice))
        # if(self.master_actor != 0):
        #     self.renderer.RemoveActor(self.master_actor);
        Lmax = 8
        if(self.odf_data.shape[3] == 15):
            Lmax = 4
        elif(self.odf_data.shape[3] == 28):
            Lmax = 6
        elif(self.odf_data.shape[3] == 45):
            Lmax = 8
        elif(self.odf_data.shape[3] == 153):
            Lmax = 16
        
        which_slice = int(np.floor(which_slice*self.target_vs[2]/self.my_vs[2]))
        print('The scaled slice is ' + str(which_slice))
        
        if(which_slice >= self.odf_data.shape[2]):
            print('Cannot select this slice')
            return
        
        sf_proj = shm.sh_to_sf(self.odf_data[:,:,which_slice:which_slice+1,:],self.sphere,Lmax,basis_type='tournier07')
        print(sf_proj.shape)
        
        sf_proj = sf_proj/np.max([sf_proj.max(),1]);
        self.master_actor = vtk.vtkAppendPolyData()            

        sf_proj = np.moveaxis(sf_proj,3,0)
        for vid_x in np.arange(0,sf_proj.shape[1],subsamp_fac):#range(0,my_odf.shape[0]):
            for vid_y in np.arange(0,sf_proj.shape[2],subsamp_fac):
                S = sf_proj[:,vid_x,vid_y,0]#.flatten()
                if(S.max() == 0):
                    continue
                
                c_pdata = vtk.vtkPolyData()
                vertices = self.sphere.vertices.copy()
                vertices = vertices/vertices.max()
                colors = vertices.copy()*255
                for i in range(0,3):
                    vertices[:,i] = vertices[:,i]*S
                vertices[:,0] = vertices[:,0]*subsamp_fac*self.scale[0]+vid_x*self.my_vs[0]+self.origin[0]
                vertices[:,1] = vertices[:,1]*subsamp_fac*self.scale[1]+vid_y*self.my_vs[1]+self.origin[1]
                vertices[:,2] = vertices[:,2]*subsamp_fac*self.scale[2]+which_slice*self.my_vs[2]+self.origin[2]
                    
                utils.set_polydata_vertices(c_pdata,vertices)
                utils.set_polydata_triangles(c_pdata,self.sphere.faces)
                utils.set_polydata_colors(c_pdata,colors)
                        
                self.master_actor.AddInputData(c_pdata)

        # odf_actor = utils.get_actor_from_polydata(master_actor);#vtk.vtkRenderer()
        # cleanFilter = vtk.vtkCleanPolyData()
        # cleanFilter.SetInputConnection(self.master_actor.GetOutputPort())
        mapper = vtk.vtkPolyDataMapper()
        # mapper.SetInputConnection(cleanFilter.GetOutputPort())
        mapper.SetInputConnection(self.master_actor.GetOutputPort())

        self.SetMapper(mapper)
        self.can_update_rendering = 1
        self.Modified()
        self.renderer.Render()

