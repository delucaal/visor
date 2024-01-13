# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:58:23 2019

@author: user
"""

import vtk
import numpy as np
from pymatreader import read_mat

MatFile = read_mat('tra.mat');
Tracts = np.asarray(MatFile['Tracts']);

points = vtk.vtkPoints();
lines = vtk.vtkCellArray();
Colors = vtk.vtkUnsignedCharArray();
Colors.SetNumberOfComponents(3);
Colors.SetName("Colors");

color_mode = 0;

if(color_mode == 0):
    # Color the lines according to start-endpoint
    idx = 0;
    for i in range(0,Tracts.shape[0]):
    #    line = vtk.vtkLine();
        lines.InsertNextCell(Tracts[i].shape[0]);
        for j in range(0,Tracts[i].shape[0]):
            points.InsertNextPoint(Tracts[i][j,(1,0,2)]);
            #line.GetPointIds().SetId(j,idx);
            lines.InsertCellPoint(idx);
            idx+=1;
        p1 = Tracts[i][0,:];
        p2 = Tracts[i][-1,:];
        v = np.abs(p2-p1);
        v = v/np.linalg.norm(v,2);
        #lines.InsertNextCell(line);
        Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255);
else:
    # Color the lines per segment
    idx = 0;
    tracts_step = 1000000;
    for i in range(0,Tracts.shape[0]):
    #    line = vtk.vtkLine();
        end_point = np.min((tracts_step,Tracts[i].shape[0]));
        
        for j in range(1,end_point):
            p1 = Tracts[i][j-1,(1,0,2)];
            p2 = Tracts[i][j,(1,0,2)];
            v = np.abs(p2-p1);
            v = v/np.linalg.norm(v,2);
            lines.InsertNextCell(2);
            points.InsertNextPoint(p1);
            lines.InsertCellPoint(idx);
            points.InsertNextPoint(p2);
            lines.InsertCellPoint(idx+1);
            Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255);
            idx+=2;

data = vtk.vtkPolyData();
data.SetPoints(points);
data.SetLines(lines);
data.GetCellData().SetScalars(Colors);

mapper = vtk.vtkPolyDataMapper();
mapper.SetInputDataObject(data);
actor = vtk.vtkActor();
actor.SetMapper(mapper);
#actor.GetProperty().SetEdgeVisibility(1);
#actor.GetProperty().SetEdgeColor(0.9,0.9,0.4);
actor.GetProperty().SetRenderLinesAsTubes(1);
#actor.GetProperty().SetRenderPointsAsSpheres(1);
actor.GetProperty().SetLineWidth(5);
#actor.GetProperty().SetVertexVisibility(1);
#actor.GetProperty().SetVertexColor(0.5,1.0,0.8);
#actor.GetProperty().SetRepresentationToPoints()
#actor.GetProperty().SetColor(0.0,1.0,0.0) 
actor.GetProperty().SetLighting(1);
actor.GetProperty().SetInterpolationToGouraud();

renWin = vtk.vtkRenderWindow()
window_size = 1024

renderer = vtk.vtkRenderer()
renderer.AddActor(actor);
renWin.AddRenderer(renderer)

camera = vtk.vtkCamera()
renderer.SetActiveCamera(camera)
renderer.ResetCamera()

renWin.SetSize(window_size, window_size)
iren = vtk.vtkRenderWindowInteractor()
style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)
iren.SetRenderWindow(renWin)

renderer.ResetCameraClippingRange()
renWin.Render()

iren.Initialize()
iren.Start() 
