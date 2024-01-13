# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:10:40 2020

@author: user
"""

import os
import nibabel as nib
from dipy.data import fetch_bundles_2_subjects
from fury import window, actor, ui

import vtk
import numpy as np
from pymatreader import read_mat



class VisorMainApp:
    window_open = False
    current_actor = 0;
    cdir = '';
    actors_list = [];
    
    def __init__(self):
        print('init')
        self.show_m = window.ShowManager(title='Visor', size=(1200, 900))
        self._setup_ui();
        self.cdir = os.getcwd();
        
    def _setup_ui(self):
        print('_setup_ui')
        if(self.cdir == ''):
            self.cdir = os.getcwd();
        # panel = ui.Panel2D(size=(300, 900), color=(1, 1, 1), align="center")
        # panel.center = (500, 400)
        self.text = ui.TextBlock2D(text='Load tract')
        self.text2 = ui.TextBlock2D(text='Load all tracts')
        self.text3 = ui.TextBlock2D(text='Delete all tracts')
        self.text.center = (50,700);
        self.text2.center = (50,600);
        self.text3.center = (50,500);
        # panel.add_element(text, (50, 500))
        # panel.add_element(text2, (180, 600))

        self.text.on_left_mouse_button_clicked = self._file_clicked
        self.text2.on_left_mouse_button_clicked = self._all_files_clicked
        self.text3.on_left_mouse_button_clicked = self._delete_all_tracts

        self.mymenu = ui.FileMenu2D(directory_path=self.cdir,multiselection=False,size=(300,300))
        # self.mymenu.listbox.down_button_callback = self._file_clicked;
        # panel.add_element(self.mymenu,(0,0));
        # self.show_m.scene.add(text2)
        self._add_ui();
    
    def _add_ui(self):
        self.show_m.scene.add(self.mymenu)
        self.show_m.scene.add(self.text)
        self.show_m.scene.add(self.text2)
        self.show_m.scene.add(self.text3)
        # text2.on_left_mouse_button_clicked = self._delete_all_tracts
        # self.show_m.scene.add(self);
        
    def _file_clicked(self,i_ren, _obj, _button):
        print('Clicked')
        # A = self.mymenu.get_file_names();
        SEL = self.mymenu.current_directory + '/' + self.mymenu.listbox.selected[0];
        Q = SEL[len(SEL)-4:len(SEL)]
        if(Q == '.mat' or Q == '.MAT'):
            self.LoadAndDisplayTract(SEL,colorby='fe_seg');
        
    def _all_files_clicked(self,i_ren, _obj, _button):
        print('Load all')
        A = self.mymenu.get_file_names();
        for SEL in A:
            Q = SEL[len(SEL)-4:len(SEL)]
            if(Q == '.mat' or Q == '.MAT'):
                try:
                    self.LoadAndDisplayTract(self.mymenu.current_directory + '/' + SEL,colorby='random');
                except:
                    print('Skipping ' + SEL + ' due to errors');
            
    def _delete_all_tracts(self,i_ren, _obj, _button):
        print('delete tracts')
        # if(self.current_actor != 0):
            # self.show_m.scene.rm(self.current_actor);
            # self.current_actor = 0;
        # self.cdir = self.mymenu.current_directory;
        # self.show_m.scene.clear();
        # self._setup_ui();
        # self._add_ui();
        for actor in self.actors_list:
            self.show_m.scene.rm(actor);
            
        self.actors_list = [];
        self.show_m.render();
        
        print('C');       
        
    def OpenWindow(self):
        self.show_m.initialize()
        self.show_m.scene.reset_camera()
        self.show_m.scene.set_camera(position=(0, 0, 200))
        self.show_m.scene.reset_clipping_range()
        self.show_m.scene.azimuth(30)
        self.show_m.start()
        self.window_open = True;
        
    def LoadAndDisplayTract(self,filename,colorby='fe'):
        print('Going to load ' + filename)
        MatFile = read_mat(filename);
        Tracts = np.asarray(MatFile['Tracts']);
        
        points = vtk.vtkPoints();
        lines = vtk.vtkCellArray();
        Colors = vtk.vtkUnsignedCharArray();
        Colors.SetNumberOfComponents(3);
        Colors.SetName("Colors");
        
        if(colorby == 'fe'):
            color_mode = 0;
        elif(colorby == 'fe_seg'):
            color_mode = 1;   
        elif(colorby == 'random'):
            color_mode = 2;
            my_color = [np.random.randint(low=1,high=255),np.random.randint(low=1,high=255),np.random.randint(low=1,high=255)];
        
        if(color_mode == 0):
            # Color the lines according to start-endpoint
            idx = 0;
            for i in range(0,Tracts.shape[0]):
                lines.InsertNextCell(Tracts[i].shape[0]);
                for j in range(0,Tracts[i].shape[0]):
                    points.InsertNextPoint(Tracts[i][j,(1,0,2)]);
                    lines.InsertCellPoint(idx);
                    idx+=1;
                p1 = Tracts[i][0,:];
                p2 = Tracts[i][-1,:];
                v = np.abs(p2-p1);
                v = v/np.linalg.norm(v,2);
                Colors.InsertNextTuple3(v[0]*255,v[1]*255,v[2]*255);
        elif(color_mode == 1):
            # Color the lines per segment
            idx = 0;
            tracts_step = 1000000;
            for i in range(0,Tracts.shape[0]):
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
        elif(color_mode == 2):
            # Color the lines per segment
            idx = 0;
            for i in range(0,Tracts.shape[0]):
                lines.InsertNextCell(Tracts[i].shape[0]);
                for j in range(0,Tracts[i].shape[0]):
                    points.InsertNextPoint(Tracts[i][j,(1,0,2)]);
                    lines.InsertCellPoint(idx);
                    idx+=1;

                Colors.InsertNextTuple3(my_color[0],my_color[1],my_color[2]);
                    
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
        actor.GetProperty().SetLineWidth(2);
        #actor.GetProperty().SetVertexVisibility(1);
        #actor.GetProperty().SetVertexColor(0.5,1.0,0.8);
        #actor.GetProperty().SetRepresentationToPoints()
        #actor.GetProperty().SetColor(0.0,1.0,0.0) 
        actor.GetProperty().SetLighting(1);
        actor.GetProperty().SetInterpolationToGouraud();
                
        # if(self.current_actor != 0):
        #     self.show_m.scene.rm(self.current_actor);
        self.actors_list.append(actor);
        self.current_actor = actor;
        self.show_m.scene.add(actor);
        self.show_m.scene.reset_camera()
        self.show_m.scene.set_camera(position=(0, 0, 200))
        self.show_m.scene.reset_clipping_range()
        self.show_m.scene.azimuth(30)
        self.show_m.render();
        print('Done')


vapp = VisorMainApp();
vapp.OpenWindow();
