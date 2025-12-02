#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 18:29:50 2020

@author: albdl
"""

from pymatreader import read_mat
import numpy as np
import time
from dipy.io.stateful_tractogram import StatefulTractogram
from dipy.io.streamline import load_tractogram
from vtk import vtkPolyDataReader
from vtkmodules.util import numpy_support
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import nibabel as nib

class VisorIO(object):
    
    @staticmethod
    def LoadMATTractography(filename,max_tracts=1e10,affine=None,std_reorient=True):
        t = time.time()
        MatFile = read_mat(filename,variable_names=['Tracts','TractMask','VDims'])
        elapsed = time.time() - t
        print('Loading of MAT took ' + str(elapsed) + 's')
        t = time.time()
        
        Tracts = MatFile['Tracts']#np.asarray(MatFile['Tracts']);
        TractMask = MatFile['TractMask']
        VD = MatFile['VDims']        
        #Shift = affine[0:3,-1]
        Shift = affine[0:3,-1]
        # for i in range(0,min(Tracts.shape[0],max_tracts)):
        if(std_reorient):
            for i in range(0,min(len(Tracts),max_tracts)):
                P = Tracts[i]
                # P[:,0] = TractMask.shape[0]*VD[1]-P[:,0]
                # P[:,1] = TractMask.shape[1]*VD[0]-P[:,1]
                P[:,0] = -P[:,0]+TractMask.shape[0]*VD[1] + Shift[1]
                P[:,1] = -P[:,1]+TractMask.shape[1]*VD[0] + Shift[0]
                P[:,2] = Shift[2]+P[:,2]
                Tracts[i] = P
        
        return Tracts
    
    @staticmethod
    def LoadTRKTractography(filename,max_tracts=1e10,affine=None,size4centering=None,downsampling_factor=1,max_tracts_load=10e3):
        Tractogram = load_tractogram(filename,filename)
        
        Tracts = Tractogram.streamlines[0:int(downsampling_factor*max_tracts_load):downsampling_factor,:]
        VD = np.diag(Tractogram.affine)[0:3]
            
        if(affine is None):
            Shift = [0,0,0]
        else:
            Shift = [0,0,0]#Tractogram.affine[0:3,-1]    
        # for i in range(0,min(Tracts.shape[0],max_tracts)):
        for i in range(0,min(len(Tracts),max_tracts)):
            P = Tracts[i]
            P[:,0] = Shift[0] + P[:,0]#/VD[0] #TractMask.shape[1]
            P[:,1] = Shift[1] + P[:,1]#/VD[1] #TractMask.shape[0]
            P[:,2] = Shift[2] + P[:,2]#/VD[2] 
            Tracts[i] = P[:,[1,0,2]]
        
        return Tracts
    
    @staticmethod
    def LoadVTKTractography(filename,affine=None,size4centering=None):
        reader = vtkPolyDataReader()
        reader.SetFileName(filename)
        reader.ReadAllVectorsOn()
        reader.ReadAllScalarsOn()
        reader.ReadAllFieldsOn()
        reader.Update()
        data = reader.GetOutput()
        
        points = numpy_support.vtk_to_numpy(data.GetPoints().GetData())
        if(size4centering is None):
            shift = np.asarray([0,0,0])
        else:
            shift = np.round(np.asarray(size4centering,dtype=np.float32)/2)#+np.asarray([0,0,0])
        shift = np.matmul(affine[0:3,0:3],np.transpose(shift))
        print(shift) 
        Tracts = []
        Lines = data.GetLines()
        Lines.InitTraversal()
        all_line_ids = vtk.vtkIdList()
        while(Lines.GetNextCell(all_line_ids)):
            #print('Line has ' + str(all_line_ids.GetNumberOfIds()) + ' points');
            #p1 = points[all_line_ids.GetId(0),:]
            #p2 = points[all_line_ids.GetId(all_line_ids.GetNumberOfIds()-1),:] (1,0,2)
            P = points[all_line_ids.GetId(0):all_line_ids.GetId(all_line_ids.GetNumberOfIds()-1),:]
            if(affine is not None):
                for ij in range(0,P.shape[0]):
                    P[ij,:] = P[ij,:] + shift
            Tracts.append(P[:,(1,0,2)])
            
        return Tracts
    
    @staticmethod
    def GetPointsLinesOfPolyData(polydata):
        vtp = polydata.GetLines()
        points = vtk_to_numpy(polydata.GetPoints().GetData())
        vtp.InitTraversal()
        all_line_ids = vtk.vtkIdList()      
        Lines = np.zeros((polydata.GetNumberOfLines(),2))  
        count = 0
        while(vtp.GetNextCell(all_line_ids)):
            #print('Line has ' + str(all_line_ids.GetNumberOfIds()) + ' points')
            Lines[count,:] = [all_line_ids.GetId(0),all_line_ids.GetId(all_line_ids.GetNumberOfIds()-1)]
            count += 1
            
        return points,Lines
    
    def load_gifti_as_vtk_polydata(filename):
        # Carica il GIFTI
        gii = nib.load(filename)

        # Estrai coordinate e triangoli
        coords = None
        faces = None

        for da in gii.darrays:
            if da.intent == 1008: #"NIFTI_INTENT_POINTSET":   # coordinate
                coords = da.data
            elif da.intent == 1009: #"NIFTI_INTENT_TRIANGLE": # triangoli
                faces = da.data

        if coords is None or faces is None:
            raise ValueError("Il file GIFTI non contiene mesh (POINTSET + TRIANGLE).")

        # Converte la geometria in VTK
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(coords.shape[0])
        for i, (x, y, z) in enumerate(coords):
            points.SetPoint(i, float(x), float(y), float(z))

        polys = vtk.vtkCellArray()
        for tri in faces:
            polys.InsertNextCell(3)
            polys.InsertCellPoint(int(tri[0]))
            polys.InsertCellPoint(int(tri[1]))
            polys.InsertCellPoint(int(tri[2]))

        # Crea un vtkPolyData
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(polys)

        # Normali (opzionale ma consigliato)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.Update()

        return normals.GetOutput()
