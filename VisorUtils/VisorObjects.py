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
from concurrent.futures import ThreadPoolExecutor

class ROIObject(object):
    TotalObjects = 0
    
    def __init__(self):
        self.ReferenceFile = ''
        self.Type = ''
        self.Center = [0,0,0]
        self.Name = 'ROI' + str(ROIObject.TotalObjects)
        self.actor = 0
        self.source = 0
        self.enabled = False
        
        ROIObject.TotalObjects += 1
        
    def InitSphereROI(self,center=[0,0,0],radius=1.0,color=[255,0,0]):
        # create source
        self.source = vtk.vtkSphereSource()
        self.source.SetCenter(center[0],center[1],center[2])
        self.source.SetRadius(radius)
        self.source.SetThetaResolution(32)
        self.source.SetPhiResolution(32)
        
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
        
    def ActorDefaultProps(self):
         actor = self.actor
         #actor.GetProperty().SetEdgeVisibility(1)
         #actor.GetProperty().SetEdgeColor(0.9,0.9,0.4)
         actor.GetProperty().SetRenderLinesAsTubes(1)
         #actor.GetProperty().SetRenderPointsAsSpheres(1)
         actor.GetProperty().SetLineWidth(4)
         #actor.GetProperty().SetVertexVisibility(1)
         #actor.GetProperty().SetVertexColor(0.5,1.0,0.8)
         #actor.GetProperty().SetRepresentationToPoints()
         #actor.GetProperty().SetColor(0.0,1.0,0.0) 
         actor.GetProperty().SetAmbient(0.05)
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
         
    def ToggleEnabled(self):
        self.enabled = not self.enabled        
        
class ROIgroupsObject(object):
    def __init__(self, name='Group'):
        self.name = name
        self.rois_list = []
        self.target_tracts = []
                 
class ImageObject(object):
        
    def __init__(self, filename, shortName, target_vs=0, minVal=0, maxVal=255, alpha=255, colormap='gray'):
        data = nib.load(filename)
        self.ReferenceFile = filename

        affine = data.affine
        self.origin = affine[0:3,3]
        #affine[0:3,3] = 0
        print(self.origin)

        taffine = affine
        #if(type(target_vs) == int or type(target_vs) == float):
        #    taffine = affine
        #else:
        #    taffine[0:3,0:3] = np.diag(target_vs)
        dataV = resample_img(data,target_affine=taffine,interpolation='nearest')
        dataV = dataV.get_fdata()
        if(dataV.ndim == 4):
            dataV = dataV[:,:,:,0]
        
        self.data = dataV
        self.affine = taffine
        self.name = shortName
        self.minVal = minVal
        self.maxVal = maxVal
        self.alpha = alpha
        self.colormap = colormap
        
        self.UpdateLUT()

    def UpdateMinMax(self,minclip=0,maxclip=255):
        self.minVal = minclip
        self.maxVal = maxclip
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
            Tracts = VisorIO.LoadMATTractography(filename, max_tracts=max_tracts,affine=affine)
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
        
        self.data = self.PreparePolydataGivenPointsAndLines_fast(Tracts,color_mode=color_mode,my_color=my_color,max_tracts=max_tracts)        
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputDataObject(self.data)
        actor = vtk.vtkActor()
        actor.SetMapper(self.mapper)        
        
        elapsed = time.time() - t
        print('The creation of the VTK actor took ' + str(elapsed) + 's')
        self.actor = actor
        self.color_mode = color_mode
        self.ActorDefaultProps()
        self.actor.SetPickable(False)
        
        self.original_colors = vtk.vtkUnsignedCharArray()
        self.original_colors.DeepCopy(self.data.GetPointData().GetScalars())
        
        self.mask = None
        self.ROIs = []
        
    def PreparePolydataGivenPointsAndLines_fast(self,Tracts, color_mode=0, my_color=[255,255,255], max_tracts=1e5):
        n_tracts = min(len(Tracts), int(max_tracts))

        # total points
        lengths = [t.shape[0] for t in Tracts[:n_tracts]]
        total_points = sum(lengths)

        # preallocate
        points_np = np.zeros((total_points, 3), dtype=np.float32)
        colors_np = np.zeros((total_points, 4), dtype=np.uint8)

        lines = vtk.vtkCellArray()
        idx = 0

        for i in range(n_tracts):
            fiber = Tracts[i]
            n_pts = fiber.shape[0]
            if n_pts <= 0:
                continue

            # Create polyline cell
            line = vtk.vtkPolyLine()
            line.GetPointIds().SetNumberOfIds(n_pts)
            for j in range(n_pts):
                line.GetPointIds().SetId(j, idx + j)
            lines.InsertNextCell(line)

            # Insert points (swap order as in your original code)
            pts = fiber[:, (1, 0, 2)].astype(np.float32)
            points_np[idx:idx + n_pts, :] = pts

            # Compute colors exactly like your original loop
            if color_mode == 0:
                # whole-line direction color (start -> end), absolute, normalized
                p1 = fiber[0, :]
                p2 = fiber[-1, :]
                v = np.abs(p2 - p1)
                nrm = np.linalg.norm(v)
                if nrm > 0:
                    v = v / nrm
                rgb = (v * 255).astype(np.uint8)
                colors_np[idx:idx + n_pts, :3] = rgb
                colors_np[idx:idx + n_pts, 3] = 255

            elif color_mode == 1:
                # per-segment direction: for point j use direction from j to j+1,
                # last point: use zero vector (like your original) or repeat last segment
                if n_pts == 1:
                    # single point fiber -> color zero
                    colors_np[idx, :3] = np.array([0, 0, 0], dtype=np.uint8)
                    colors_np[idx, 3] = 255
                else:
                    # differences in original coordinate order (no swap), as in your code
                    segs = np.diff(fiber, axis=0)  # shape (n_pts-1, 3)
                    norms = np.linalg.norm(segs, axis=1, keepdims=True)
                    norms[norms == 0] = 1.0
                    dirs = np.abs(segs / norms)  # (n_pts-1, 3)
                    seg_rgb = (dirs * 255).astype(np.uint8)  # (n_pts-1, 3)
                    # assign per-point: for points 0..n_pts-2 use seg_rgb[0..], for last point repeat last seg
                    colors_np[idx:idx + n_pts - 1, :3] = seg_rgb
                    colors_np[idx + n_pts - 1, :3] = seg_rgb[-1]
                    colors_np[idx:idx + n_pts, 3] = 255

            elif color_mode == 2:
                rgb = np.array(my_color, dtype=np.uint8)
                colors_np[idx:idx + n_pts, :3] = rgb
                colors_np[idx:idx + n_pts, 3] = 255

            idx += n_pts

        # Build vtkPoints from numpy
        vtk_points = vtk.vtkPoints()
        vtk_points.SetData(vtk.util.numpy_support.numpy_to_vtk(points_np, deep=True))

        # Build vtk color array properly
        vtk_colors = vtk.util.numpy_support.numpy_to_vtk(colors_np, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
        vtk_colors.SetNumberOfComponents(4)
        vtk_colors.SetName("Colors")

        # Assemble polydata
        data = vtk.vtkPolyData()
        data.SetPoints(vtk_points)
        data.SetLines(lines)
        data.GetPointData().SetScalars(vtk_colors)

        return data
        
    def AddROI(self,roi):
        self.ROIs.append(roi)
        
    def IndexOfROIByName(self,name):
        idx = -1
        for i in range(0,len(self.ROIs)):
            if(self.ROIs[i].Name == name):
                idx = i
                break
        return idx
    
    def DeleteROIByName(self,name):
        idx = self.IndexOfROIByName(name)
        if(idx != -1):
            self.ROIs.pop(idx)
        
    def PreparePolydataGivenPointsAndLines(self,Tracts,color_mode=0,my_color=[255,255,255],max_tracts=1e5):
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        Colors = vtk.vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(4)
        Colors.SetName("Colors")
        
        idx = 0
        # for i in range(0,min(Tracts.shape[0],max_tracts)):
        for i in range(0,min(len(Tracts),max_tracts)):
            if(color_mode == 0):
                # Color the lines according to start-endpoint
                p1 = Tracts[i][0,:]
                p2 = Tracts[i][-1,:]
                v = np.abs(p2-p1)
                v = v/np.linalg.norm(v,2)
                
                line = vtk.vtkPolyLine()
                line.GetPointIds().SetNumberOfIds(Tracts[i].shape[0])
                #lines.InsertNextCell(Tracts[i].shape[0])
                for j in range(0,Tracts[i].shape[0]):
                    points.InsertNextPoint(Tracts[i][j,(1,0,2)])
                    line.GetPointIds().SetId(j,idx)
                    Colors.InsertNextTuple4(v[0]*255,v[1]*255,v[2]*255,255)
                    #lines.InsertCellPoint(idx)
                    idx+=1
                lines.InsertNextCell(line)
                
            elif(color_mode == 1):
                # Color the lines per segment
                
                fiber = Tracts[i]
                n_pts = fiber.shape[0]
                line = vtk.vtkPolyLine()
                line.GetPointIds().SetNumberOfIds(n_pts)
                
                for j in range(n_pts):
                    pt = fiber[j, (1,0,2)]  # swap Y and X if needed
                    points.InsertNextPoint(pt)
                    line.GetPointIds().SetId(j, idx)
                    
                    # compute directional color
                    if j < n_pts - 1:
                        v = np.abs(fiber[j+1,:] - fiber[j,:])
                        v /= np.linalg.norm(v)
                    else:
                        v = np.array([0,0,0])
                    r, g, b = (v*255).astype(int)
                    Colors.InsertNextTuple4(r, g, b, 255)  # full alpha
                    
                    idx += 1
                
                lines.InsertNextCell(line)                    
                
            elif(color_mode == 2):
                # Single color per line
                line = vtk.vtkPolyLine()
                line.GetPointIds().SetNumberOfIds(Tracts[i].shape[0])
                #lines.InsertNextCell(Tracts[i].shape[0])
                for j in range(0,Tracts[i].shape[0]):
                    points.InsertNextPoint(Tracts[i][j,(1,0,2)])
                    line.GetPointIds().SetId(j,idx)
                    Colors.InsertNextTuple4(my_color[0],my_color[1],my_color[2],255)
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
    
    def color_tracts_by_roi_intersection_transformed(self, 
                                                    rois_list=None,
                                                    intersect_color=(1,0,0),
                                                    alpha_outside=0.1):
        """
        Color tracts that intersect ALL ROIs (logical AND) after applying transforms.

        Parameters
        ----------
        tract_polydata : vtkPolyData
            All tracts.
        tract_matrix : vtkMatrix4x4
            Transformation to apply to tract_polydata.
        roi_list : list of vtkPolyData or vtkSphereSource
            ROIs to test intersection.
        roi_matrices : list of vtkMatrix4x4
            Transformations to apply to each ROI.
        intersect_color : tuple(float, float, float)
            RGB for intersecting tracts.
        alpha_outside : float
            Opacity for non-intersecting tracts (0-1).
        """
        
        if(rois_list is None):
            rois_list = self.ROIs or []

        enc = vtk.vtkSelectEnclosedPoints()
        #enc.SetInputConnection(self.test_line_source.GetOutputPort())
        transf = vtk.vtkTransform()
        transf.SetMatrix(self.actor.GetMatrix())
        transfP = vtk.vtkTransformPolyDataFilter()
        transfP.SetTransform(transf)
        transfP.SetInputDataObject(self.data)
        transfP.Update()
        tracts_transformed = transfP.GetOutput()
                
        # Initialize combined point mask (all True for logical AND)
        # transformed_tracts: vtkPolyData of fibers (after transform)
        n_cells = tracts_transformed.GetNumberOfCells()
        LineSelector = np.ones(n_cells, dtype=bool)  # start with True

        for roi in rois_list:
            # Transform ROI
            transf2 = vtk.vtkTransform()
            transf2.SetMatrix(roi.actor.GetMatrix())
            transfP2 = vtk.vtkTransformPolyDataFilter()
            transfP2.SetTransform(transf2)
            transfP2.SetInputConnection(roi.source.GetOutputPort())
            transfP2.Update()
            
            # Select points inside current ROI
            enc = vtk.vtkSelectEnclosedPoints()
            enc.SetInputDataObject(tracts_transformed)
            enc.SetSurfaceConnection(transfP2.GetOutputPort())
            enc.Update()
            
            insideArray = vtk_to_numpy(enc.GetOutput().GetPointData().GetArray("SelectedPoints")).astype(bool)
            
            # Now compute per-fiber mask for this ROI
            fiber_mask = np.zeros(n_cells, dtype=bool)
            for cell_id in range(n_cells):
                ids = tracts_transformed.GetCell(cell_id).GetPointIds()
                if np.any([insideArray[ids.GetId(j)] for j in range(ids.GetNumberOfIds())]):
                    fiber_mask[cell_id] = True

            # AND across ROIs
            LineSelector = np.logical_and(LineSelector, fiber_mask)
                
        print(LineSelector.sum())
        self.ColorSpecificLinesTemp4(LineSelector)
        self.actor.Modified()

    def color_tracts_by_roi_intersection_optimized(self, rois_list, alpha_outside=0.1):
        tracts = self.data
        n_cells = tracts.GetNumberOfCells()
        LineSelector = np.ones(n_cells, dtype=bool)

        if(rois_list is None):
            rois_list = self.ROIs or []

        # Transform fibers globally
        transf = vtk.vtkTransform()
        transf.SetMatrix(self.actor.GetMatrix())
        transfP = vtk.vtkTransformPolyDataFilter()
        transfP.SetTransform(transf)
        transfP.SetInputData(tracts)
        transfP.Update()
        tracts_transformed = transfP.GetOutput()

        # Precompute cell bounds
        cell_bounds_array = np.zeros((n_cells, 6))
        for cid in range(n_cells):
            b = tracts_transformed.GetCell(cid).GetBounds()
            cell_bounds_array[cid, :] = b

        active_rois = False
        for roi in rois_list:
            if(roi.enabled == False):
                continue
            active_rois = True            
            # Transform ROI
            transf2 = vtk.vtkTransform()
            transf2.SetMatrix(roi.actor.GetMatrix())
            transfP2 = vtk.vtkTransformPolyDataFilter()
            transfP2.SetTransform(transf2)
            transfP2.SetInputConnection(roi.source.GetOutputPort())
            transfP2.Update()
            roi_poly = transfP2.GetOutput()

            # Build OBBTree
            obb = vtk.vtkOBBTree()
            obb.SetDataSet(roi_poly)
            obb.BuildLocator()

            # ROI bounding box
            roi_bbox = vtk.vtkBoundingBox(roi_poly.GetBounds())

            fiber_mask = np.zeros(n_cells, dtype=bool)
            intersect_points = vtk.vtkPoints()

            # ------------------------
            # Vectorized bounding box prefilter
            # ------------------------
            candidates = np.where(
                (cell_bounds_array[:, 1] >= roi_bbox.GetMinPoint()[0]) &
                (cell_bounds_array[:, 0] <= roi_bbox.GetMaxPoint()[0]) &
                (cell_bounds_array[:, 3] >= roi_bbox.GetMinPoint()[1]) &
                (cell_bounds_array[:, 2] <= roi_bbox.GetMaxPoint()[1]) &
                (cell_bounds_array[:, 5] >= roi_bbox.GetMinPoint()[2]) &
                (cell_bounds_array[:, 4] <= roi_bbox.GetMaxPoint()[2])
            )[0]

            # ------------------------
            # Only check candidate fibers
            # ------------------------
            for cell_id in candidates:
                cell = tracts_transformed.GetCell(cell_id)
                pts = cell.GetPoints()
                hit = False
                for j in range(pts.GetNumberOfPoints() - 1):
                    p1 = pts.GetPoint(j)
                    p2 = pts.GetPoint(j + 1)
                    if obb.IntersectWithLine(p1, p2, intersect_points, None):
                        hit = True
                        break
                fiber_mask[cell_id] = hit

            # AND logic across ROIs
            LineSelector = np.logical_and(LineSelector, fiber_mask)

        if(active_rois == True):
            print("Intersecting fibers:", LineSelector.sum())
            self.ColorSpecificLinesTemp4(LineSelector)
        else:
            print("No active ROIs, restoring original colors.")
            mapper = self.actor.GetMapper()
            poly = mapper.GetInputDataObject(0,0)
            poly.GetPointData().SetScalars(self.original_colors)
        self.actor.Modified()
        
    def color_tracts_by_roi_intersection_fast(self, rois_list, alpha_outside=0.1):
        tracts = self.data
        n_cells = tracts.GetNumberOfCells()
        LineSelector = np.ones(n_cells, dtype=bool)
        
        # Apply global transform to tracts
        transf = vtk.vtkTransform()
        transf.SetMatrix(self.actor.GetMatrix())
        transfP = vtk.vtkTransformPolyDataFilter()
        transfP.SetTransform(transf)
        transfP.SetInputData(tracts)
        transfP.Update()
        tracts_transformed = transfP.GetOutput()


        for roi in rois_list:
            # Transform ROI surface
            transf2 = vtk.vtkTransform()
            transf2.SetMatrix(roi.actor.GetMatrix())
            transfP2 = vtk.vtkTransformPolyDataFilter()
            transfP2.SetTransform(transf2)
            transfP2.SetInputConnection(roi.source.GetOutputPort())
            transfP2.Update()
            roi_poly = transfP2.GetOutput()
            # Pre-allocate box object
            bbox = vtk.vtkBoundingBox(roi_poly.GetBounds())

            # Build OBBTree for fast intersection
            obb = vtk.vtkOBBTree()
            obb.SetDataSet(roi_poly)
            obb.BuildLocator()

            fiber_mask = np.zeros(n_cells, dtype=bool)
            intersect_points = vtk.vtkPoints()

            cell_bounds = [0.0]*6
            for cell_id in range(n_cells):
                cell = tracts_transformed.GetCell(cell_id)
                # --- Bounding box prefilter ---
                #cell_bounds = [0.0]*6                     # prepare list
                #tracts_transformed.GetCellBounds(cell_id, cell_bounds)  # fills the list
                #cell_bbox = vtk.vtkBoundingBox(cell_bounds)             # construct bounding box
                #if not bbox.IntersectBox(cell_bbox):
                #    continue  # skip fiber

                # --- Check line segments with OBBTree ---
                pts = cell.GetPoints()
                hit = False
                for j in range(pts.GetNumberOfPoints() - 1):
                    p1 = pts.GetPoint(j)
                    p2 = pts.GetPoint(j + 1)
                    if obb.IntersectWithLine(p1, p2, intersect_points, None):
                        hit = True
                        break
                fiber_mask[cell_id] = hit

            # AND logic across ROIs
            LineSelector = np.logical_and(LineSelector, fiber_mask)

        print("Intersecting fibers:", LineSelector.sum())
        self.ColorSpecificLinesTemp4(LineSelector)
        self.actor.Modified()
        
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
        
    def ColorSpecificLinesTemp3(self, selected_lines):
        """
        Color fibers based on a boolean array per fiber.
        selected_lines: boolean array of length = number of cells
        """
        mapper = self.actor.GetMapper()
        polydata = mapper.GetInputDataObject(0,0)
        n_points = polydata.GetNumberOfPoints()
        
        Colors = vtk.vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(4)
        Colors.SetName("Colors")
        
        # Assign color per point according to the cell it belongs to
        cell_point_ids = vtk.vtkIdList()
        line_idx = 0
        unselected_alpha = 25
        if(selected_lines.sum() == 0):
            unselected_alpha = 255
        for cell_id in range(polydata.GetNumberOfCells()):
            polydata.GetCellPoints(cell_id, cell_point_ids)
            color = [255, 0, 0, 255] if selected_lines[cell_id] else [255, 255, 255, unselected_alpha]
            for j in range(cell_point_ids.GetNumberOfIds()):
                Colors.InsertNextTuple4(*color)
            line_idx += 1
        
        # Attach color array to points
        polydata.GetPointData().SetScalars(Colors)
        #polydata.GetCellData().SetScalars(Colors)
        polydata.Modified()
        
    def ColorSpecificLinesTemp4(self, selected_lines, alpha_outside=20):
        """
        selected_lines: boolean array of length = number of cells
                        True = intersects ROI
        """
        mapper = self.actor.GetMapper()
        polydata = mapper.GetInputDataObject(0, 0)
        
        # Get existing colors (assuming 4 components per point)
        Colors = polydata.GetPointData().GetScalars()
        if Colors.GetNumberOfComponents() == 3:
            # Convert to 4 components
            newColors = vtk.vtkUnsignedCharArray()
            newColors.SetNumberOfComponents(4)
            newColors.SetName("Colors")
            for i in range(Colors.GetNumberOfTuples()):
                r, g, b = Colors.GetTuple3(i)
                newColors.InsertNextTuple4(r, g, b, 255)
            Colors = newColors
        
        # Prepare new array
        newColors = vtk.vtkUnsignedCharArray()
        newColors.SetNumberOfComponents(4)
        newColors.SetName("Colors")
        
        # Traverse each line
        cell_point_ids = vtk.vtkIdList()
        for cell_id in range(polydata.GetNumberOfCells()):
            polydata.GetCellPoints(cell_id, cell_point_ids)
            # Determine alpha for this line
            alpha = 255 if selected_lines[cell_id] else alpha_outside
            for j in range(cell_point_ids.GetNumberOfIds()):
                idx = cell_point_ids.GetId(j)
                r, g, b, _ = Colors.GetTuple4(idx)
                #if(alpha < 255):
                #    r = 255
                #    g = 255
                #    b = 255
                newColors.InsertNextTuple4(r, g, b, alpha)
        
        polydata.GetPointData().SetScalars(newColors)
        polydata.Modified()        
        
    def ColorSpecificLinesTemp4_fast(self, selected_lines, alpha_outside=0):
        """
        Faster version using NumPy, for independent fibers.
        Preserves exact behavior:
        - fibers intersecting ROI: keep original RGB, alpha=255
        - fibers outside ROI: white, alpha=alpha_outside
        """
        mapper = self.actor.GetMapper()
        polydata = mapper.GetInputDataObject(0, 0)
        n_points = polydata.GetNumberOfPoints()

        # Get colors as NumPy array
        Colors = polydata.GetPointData().GetScalars()
        colors_np = vtk.util.numpy_support.vtk_to_numpy(Colors)

        # Convert to RGBA if needed
        if Colors.GetNumberOfComponents() == 3:
            colors_np = np.hstack([colors_np, 255 * np.ones((n_points, 1), dtype=np.uint8)])
        
        colors_np = colors_np.astype(np.uint8)
        new_colors = colors_np.copy()

        # Per-cell point indices
        n_cells = polydata.GetNumberOfCells()
        cell_point_ids = [polydata.GetCell(i).GetPointIds() for i in range(n_cells)]

        # Apply coloring
        for cell_id, pid_list in enumerate(cell_point_ids):
            indices = [pid_list.GetId(j) for j in range(pid_list.GetNumberOfIds())]
            if selected_lines[cell_id]:
                new_colors[indices, 3] = 255
            else:
                new_colors[indices, 0:3] = 255
                new_colors[indices, 3] = int(alpha_outside)  # ensure integer

        # Push to VTK
        vtk_array = vtk.util.numpy_support.numpy_to_vtk(new_colors, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
        vtk_array.SetNumberOfComponents(4)
        vtk_array.SetName("Colors")
        polydata.GetPointData().SetScalars(vtk_array)
        polydata.Modified()
                        
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
        actor.GetProperty().SetAmbient(0.05)
        actor.GetProperty().SetLighting(1)
        actor.GetProperty().SetInterpolationToGouraud()
        actor.GetProperty().SetDiffuse(.8)
        actor.GetProperty().SetSpecular(.5)
        actor.GetProperty().SetSpecularColor(1.0,1.0,1.0)
        actor.GetProperty().SetSpecularPower(30.0)
        
        #shader_property = actor.GetShaderProperty()
        #shader_property.AddShaderReplacement(
        #   vtk.vtkShader.Fragment,
        #   "//VTK::Light::Impl",  # replace VTK's lighting implementation
        #   True,
        #   self.custom_fragment_code(),
        #   False
        #)              
        actor.Modified()    

    def ActorHighlightedProps(self):
         current_actor = self.actor
         current_actor.GetProperty().SetColor(1.0, 0.0, 0.0)
         current_actor.GetProperty().SetDiffuse(1.0)
         current_actor.GetProperty().SetSpecular(0.0)          
         current_actor.GetProperty().SetOpacity(1.0)     
    
    def EnableUndersamplingWithFactor(self,factor=2): 
        if(self.mask is not None):
            self.mask.SetOnRatio(factor)
            self.mask.Update()
            self.mapper.SetInputConnection(self.mask.GetOutputPort()) 
            self.actor.Modified()
            return
        else:
            self.mask = vtk.vtkMaskPolyData()
            self.mask.SetInputData(self.data)         # your polydata with all streamlines
            self.mask.SetOnRatio(factor)                  # keep 1 out of every 10 lines
            self.mask.Update()

            self.mapper.SetInputConnection(self.mask.GetOutputPort())            
            self.actor.Modified()    
    
    def DisableUndersampling(self):
        if(self.mask is not None):
            self.mapper.SetInputData(self.data)
            self.actor.Modified()
            self.mask = None
    
    def custom_fragment_code(self):
        shader = 2
        if(shader == 1):
            return """
            //VTK::Light::Impl

            // Inputs from VTK's vertex shader
            vec3 N = normalize(normalVCVSOutput);
            vec3 V = normalize(-vertexVC.xyz);
            vec3 L = normalize(vec3(0.4, 0.6, 1.0));

            // Use per-vertex color as base
            vec3 baseColor = vertexColorVSOutput.rgb;

            // Lighting terms
            float NdotL = max(dot(N, L), 0.0);
            float ambient = 0.3;

            // Specular highlight
            vec3 R = reflect(-L, N);
            float spec = pow(max(dot(V, R), 0.0), 64.0) * 0.8;

            // Fresnel edge tint for metallic sheen
            float fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.0);
            vec3 metallicColor = mix(baseColor, vec3(1.0), fresnel * 0.3);

            // Combine diffuse + specular + ambient
            vec3 colorOut = metallicColor * (ambient + NdotL) + vec3(spec);

            // Output final color
            gl_FragData[0] = vec4(colorOut, opacity);
            """
        elif(shader == 2):
            return """
            //VTK::Light::Impl

            vec3 N = normalize(normalVCVSOutput);
            vec3 V = normalize(-vertexVC.xyz);
            vec3 L = normalize(vec3(0.4, 0.6, 1.0));

            vec3 baseColor = vertexColorVSOutput.rgb;

            // Direction-based anisotropic term
            float NdotL = max(dot(N, L), 0.0);
            vec3 R = reflect(-L, N);
            float tangentSpec = pow(max(dot(V, R), 0.0), 8.0);
            float anisotropy = pow(abs(dot(N, vec3(0.0, 1.0, 0.0))), 0.3);

            // Combine
            float ambient = 0.3;
            vec3 colorOut = baseColor * (ambient + NdotL * (0.7 + 0.3 * anisotropy)) + vec3(tangentSpec);
            gl_FragData[0] = vec4(colorOut, opacity);
            """
        elif(shader == 3):
            return """
            //VTK::Light::Impl
            vec3 glowColor = vertexColorVSOutput.rgb;
            float intensity = pow(max(dot(normalize(normalVCVSOutput), vec3(0.0, 0.0, 1.0)), 0.0), 0.3);

            // strong center glow, soft falloff
            float glow = 0.6 + 0.4 * intensity;
            vec3 colorOut = glowColor * glow;

            gl_FragData[0] = vec4(colorOut, 1.0);
            """
        elif(shader == 4):
            return """"
            //VTK::Light::Impl

            vec3 N = normalize(normalVCVSOutput);
            vec3 V = normalize(-vertexVC.xyz);
            vec3 L = normalize(vec3(0.2, 0.4, 1.0));

            float NdotL = max(dot(N, L), 0.0);
            float NdotV = max(dot(N, V), 0.0);

            vec3 baseColor = vertexColorVSOutput.rgb;
            vec3 scatter = baseColor * (0.3 + 0.7 * pow(1.0 - NdotV, 2.0)); // backlit glow

            vec3 colorOut = baseColor * (0.3 + 0.7*NdotL) + scatter * 0.5;
            gl_FragData[0] = vec4(colorOut, opacity);    
            """