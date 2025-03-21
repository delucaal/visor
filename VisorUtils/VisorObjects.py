#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 10 09:51:33 2020

@author: albdl
"""
import time
import vtk
import nibabel as nib
from nilearn.image import resample_img
import numpy as np
from VisorUtils.IOManager import VisorIO
from vtk.util.numpy_support import vtk_to_numpy
from fury import actor,colormap as fury_colormap

class ROIObject(object):
    TotalObjects = 0
    
    def __init__(self):
        self.ReferenceFile = ''
        self.Type = ''
        self.Center = [0,0,0]
        self.Name = 'ROI' + str(ROIObject.TotalObjects)
        self.actor = 0
        self.source = 0
        
        ROIObject.TotalObjects += 1
        
    def InitSphereROI(self,center=[0,0,0],radius=1.0,color=[255,0,0]):
        # create source
        self.source = vtk.vtkSphereSource()
        self.source.SetCenter(center[0],center[1],center[2])
        self.source.SetRadius(radius)
        
        # mapper
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.source.GetOutputPort())
        
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.Type = 'Sphere'
        self.Center = center
     
    def ChangeSphereROI(self,radius=1.0):
        if(self.actor != 0 and self.source != 0):
            self.source.SetRadius(radius)
        
        
class ImageObject(object):
        
    def __init__(self, filename, shortName, target_vs=0, minVal=0, maxVal=255, alpha=255, colormap='gray'):
        data = nib.load(filename)
        self.ReferenceFile = filename

        affine = data.affine
        self.origin = affine[0:3,3]
        affine[0:3,3] = 0
        print(self.origin)

        self.affine = affine
        if(type(target_vs) == int or type(target_vs) == float):
            taffine = affine
        else:
            taffine = np.diag(target_vs)
        dataV = resample_img(data,target_affine=taffine,interpolation='nearest')
        dataV = dataV.get_fdata()
        
        self.data = dataV
        self.affine = taffine
        self.name = shortName
        self.minVal = minVal
        self.maxVal = maxVal
        self.alpha = alpha
        self.colormap = colormap
        
        self.UpdateLUT()

    def UpdateMinMax(self,minclip=0,maxclip=255):
        self.minVal = minclip;
        self.maxVal = maxclip;
        # print('New min ' + str(self.minVal) + ' max ' + str(self.maxVal))

    def UpdateLUT(self):
        cmap = fury_colormap.create_colormap(np.arange(0,256),name=self.colormap)
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(cmap.shape[0])
        lut.Build()
    
        for i in range(0,cmap.shape[0]):
            lut.SetTableValue(i,cmap[i,0],cmap[i,1],cmap[i,2],1)
        
        lut.SetRange(self.minVal/255,self.maxVal/255)
        lut.SetScaleToLinear()
        self.lut = lut


class TractographyObject(object):

    def __init__(self,filename,colorby='random',max_tracts=1e10,affine=None,size4centering=None):    
        if('.mat' in filename):
            Tracts = VisorIO.LoadMATTractography(filename, max_tracts=max_tracts)
        elif('.trk' in filename or '.tck' in filename):
            Tracts = VisorIO.LoadTRKTractography(filename, max_tracts=max_tracts,affine=affine,size4centering=size4centering)
        elif('.vtk' in filename):
            Tracts = VisorIO.LoadVTKTractography(filename,affine=affine,size4centering=size4centering)
                        
        t = time.time()
        
        if(colorby == 'fe'):
            color_mode = 0
            my_color = [255,255,255]
        elif(colorby == 'fe_seg'):
            color_mode = 1
            my_color = [255,255,255]
        elif(colorby == 'random'):
            color_mode = 2
            my_color = [np.random.randint(low=1,high=255),np.random.randint(low=1,high=255),np.random.randint(low=1,high=255)]
        
        self.data = self.PreparePolydataGivenPointsAndLines(Tracts,color_mode=color_mode,my_color=my_color,max_tracts=max_tracts)        
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputDataObject(self.data)
        actor = vtk.vtkActor()
        actor.SetMapper(self.mapper)        
        
        elapsed = time.time() - t
        print('The creation of the VTK actor took ' + str(elapsed) + 's')
        self.actor = actor
        self.color_mode = color_mode
        self.ActorDefaultProps()
        
    def PreparePolydataGivenPointsAndLines(self,Tracts,color_mode=0,my_color=[255,255,255],max_tracts=1e5):
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        Colors = vtk.vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(3)
        Colors.SetName("Colors")
        
        idx = 0
        # for i in range(0,min(Tracts.shape[0],max_tracts)):
        for i in range(0,min(len(Tracts),max_tracts)):
            if(color_mode == 0):
                # Color the lines according to start-endpoint
                lines.InsertNextCell(Tracts[i].shape[0])
                for j in range(0,Tracts[i].shape[0]):
                    points.InsertNextPoint(Tracts[i][j,(1,0,2)])
                    lines.InsertCellPoint(idx)
                    idx+=1;
                p1 = Tracts[i][0,:];
                p2 = Tracts[i][-1,:];
                v = np.abs(p2-p1)
                v = v/np.linalg.norm(v,2)
                Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255)
            elif(color_mode == 1):
                # Color the lines per segment
                tracts_step = 1000000
                end_point = np.min((tracts_step,Tracts[i].shape[0]))
                
                for j in range(1,end_point):
                    p1 = Tracts[i][j-1,(1,0,2)];
                    p2 = Tracts[i][j,(1,0,2)];
                    v = np.abs(p2-p1)
                    v = v/np.linalg.norm(v,2)
                    lines.InsertNextCell(2)
                    points.InsertNextPoint(p1)
                    lines.InsertCellPoint(idx)
                    points.InsertNextPoint(p2)
                    lines.InsertCellPoint(idx+1)
                    Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255)
                    Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255)
                    idx+=2
                    
            elif(color_mode == 2):
                # Color the lines per segment
                line = vtk.vtkPolyLine()
                line.GetPointIds().SetNumberOfIds(Tracts[i].shape[0])
                #lines.InsertNextCell(Tracts[i].shape[0])
                for j in range(0,Tracts[i].shape[0]):
                    points.InsertNextPoint(Tracts[i][j,(1,0,2)])
                    line.GetPointIds().SetId(j,idx)
                    Colors.InsertNextTuple3(*my_color)
                    #lines.InsertCellPoint(idx)
                    idx+=1
                lines.InsertNextCell(line)
                #Colors.InsertNextTuple3(my_color[0],my_color[1],my_color[2])
                    
        data = vtk.vtkPolyData()
        data.SetPoints(points)
        data.SetLines(lines)
        #data.GetCellData().SetScalars(Colors)
        data.GetPointData().SetScalars(Colors)
        return data

    def SetColorSingle(self,red=255,green=255,blue=255):
        mapper = self.actor.GetMapper()
        poly = mapper.GetInputDataObject(0,0).GetCellData()
        old_colors = poly.GetScalars()
        
        Colors = vtk.vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(3)
        Colors.SetName("Colors")
    
        for i in range(0,old_colors.GetNumberOfTuples()):
            Colors.InsertNextTuple3(red,green,blue)
        
        poly.SetScalars(Colors)        
        
    def SetColorDEC(self):
        mapper = self.actor.GetMapper()
        poly = mapper.GetInputDataObject(0,0).GetCellData()
        vtp = mapper.GetInputDataObject(0,0).GetLines()
        points = vtk_to_numpy(mapper.GetInputDataObject(0,0).GetPoints().GetData())

        Colors = vtk.vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(3)
        Colors.SetName("Colors")

        vtp.InitTraversal()
        all_line_ids = vtk.vtkIdList()        
        while(vtp.GetNextCell(all_line_ids)):
            #print('Line has ' + str(all_line_ids.GetNumberOfIds()) + ' points')
            p1 = points[all_line_ids.GetId(0),:]
            p2 = points[all_line_ids.GetId(all_line_ids.GetNumberOfIds()-1),:]
            v = np.abs(p2-p1)
            v = v/np.linalg.norm(v,2)
             #print('Iterating ' + str(v[0]) + ' ' + str(v[1]) + str(v[2]))
            Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255)
            Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255)
                    
        poly.SetScalars(Colors)
        
    def ColorSpecificLinesTemp(self,selected_lines):
        mapper = self.actor.GetMapper()
        poly = mapper.GetInputDataObject(0,0).GetCellData()
        vtp = mapper.GetInputDataObject(0,0).GetLines()
        points = vtk_to_numpy(mapper.GetInputDataObject(0,0).GetPoints().GetData())

        Colors = vtk.vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(3)
        Colors.SetName("Colors")

        vtp.InitTraversal()
        all_line_ids = vtk.vtkIdList()       
        idx = 0 

        while(vtp.GetNextCell(all_line_ids)):
            # Assign red (255, 0, 0) if 1, white (255, 255, 255) if 0
            line_ids = np.arange(all_line_ids.GetId(0), all_line_ids.GetId(all_line_ids.GetNumberOfIds()-1)+1)
            line_was_hit = np.any(selected_lines[line_ids] == 1)
            color = [255, 0, 0] if line_was_hit else [255, 255, 255]
            for i in range(0,len(line_ids)):#range(selected_lines.shape[0]):
                #color = [255, 0, 0] if selected_lines[i] == 1 else [255, 255, 255]
                Colors.InsertNextTuple3(*color)

        # Attach color array to polydata
        #poly.SetScalars(Colors)
        mapper.GetInputDataObject(0,0).GetPointData().SetScalars(Colors)    

        # Update the mapper to use per-point coloring
        #mapper.SetScalarModeToUseCellData()        
        #mapper.SetScalarModeToUsePointData()
        
    def GetPointsAndLines(self):
        mapper = self.actor.GetMapper()
        pdata = mapper.GetInputDataObject(0,0)
        points,Lines = VisorIO.GetPointsLinesOfPolyData(pdata)
        return points,Lines
            
    def ActorDefaultProps(self):
         actor = self.actor
         #actor.GetProperty().SetEdgeVisibility(1)
         #actor.GetProperty().SetEdgeColor(0.9,0.9,0.4)
         actor.GetProperty().SetRenderLinesAsTubes(1)
         #actor.GetProperty().SetRenderPointsAsSpheres(1)
         actor.GetProperty().SetLineWidth(2)
         #actor.GetProperty().SetVertexVisibility(1)
         #actor.GetProperty().SetVertexColor(0.5,1.0,0.8)
         #actor.GetProperty().SetRepresentationToPoints()
         #actor.GetProperty().SetColor(0.0,1.0,0.0) 
         actor.GetProperty().SetLighting(1)
         actor.GetProperty().SetInterpolationToGouraud()
         actor.GetProperty().SetDiffuse(.8)
         actor.GetProperty().SetSpecular(.5)
         actor.GetProperty().SetSpecularColor(1.0,1.0,1.0)
         actor.GetProperty().SetSpecularPower(30.0)
    
    def ActorHighlightedProps(self):
         current_actor = self.actor
         current_actor.GetProperty().SetColor(1.0, 0.0, 0.0)
         current_actor.GetProperty().SetDiffuse(1.0)
         current_actor.GetProperty().SetSpecular(0.0)          
         current_actor.GetProperty().SetOpacity(1.0)     