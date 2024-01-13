# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:58:23 2019

@author: user
"""

import vtk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy

reader = vtk.vtkPolyDataReader();
reader.SetFileName('example-UKF-data.vtk');
reader.Update();
data = reader.GetOutput();

points = data.GetPoints()
npts = points.GetNumberOfPoints()
points_array = vtk_to_numpy(points.GetData())

lines = data.GetLines();
lines2save = vtk_to_numpy(lines.GetData());


#fout = open('example-UKF-data.txt','wt');
#fout.write('POINTS\n');
#for pid in range(0,points_array.shape[0]):
#    fout.write('%f %f %f\n' % (points_array[pid,0],points_array[pid,1],points_array[pid,2]));
#fout.write('LINES\n');
#idx = 0;
#while(idx < lines2save.shape[0]):
#    N = lines2save[idx];
#    fout.write('%d' % (N));
#    idx+=1;
#    for fN in range(0,N):
#        fout.write('%d ' % (lines2save[idx]));
#        idx+=1;
#    fout.write('\n');
#fout.close();

Colors = vtk.vtkUnsignedCharArray();
Colors.SetNumberOfComponents(3);
Colors.SetName("Colors");

all_line_ids = vtk.vtkIdList();
lines.InitTraversal();
while(lines.GetNextCell(all_line_ids)):
    #print('Line has ' + str(all_line_ids.GetNumberOfIds()) + ' points');
    p1 = points_array[all_line_ids.GetId(0),:];
    p2 = points_array[all_line_ids.GetId(all_line_ids.GetNumberOfIds()-1),:];
    v = np.abs(p2-p1);
    v = v/np.linalg.norm(v,2);
    Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255);
    #for pointId in range(0,all_line_ids.GetNumberOfIds()):
    #    realPointId = all_line_ids.GetId(pointId);
    #    print('' + str(realPointId) + ' ');
    #print('\n');

data.GetCellData().SetScalars(Colors);
data.Modified();

mapper = vtk.vtkPolyDataMapper();
mapper.SetInputDataObject(data);
actor = vtk.vtkActor();
actor.SetMapper(mapper);
#actor.GetProperty().SetEdgeVisibility(1);
#actor.GetProperty().SetEdgeColor(0.9,0.9,0.4);
actor.GetProperty().SetRenderLinesAsTubes(1);
#actor.GetProperty().SetRenderPointsAsSpheres(1);
actor.GetProperty().SetLineWidth(3);
#actor.GetProperty().SetVertexVisibility(1);
#actor.GetProperty().SetVertexColor(0.5,1.0,0.8);
#actor.GetProperty().SetRepresentationToPoints()
#actor.GetProperty().SetColor(0.0,1.0,0.0) 
actor.GetProperty().SetLighting(1);
actor.GetProperty().SetInterpolationToGouraud ();

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
