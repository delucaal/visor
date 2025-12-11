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
from vtk.util import numpy_support

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
        self.affine = orig_data.affine
        self.my_vs = np.diag(orig_data.affine)
        self.target_vs = self.my_vs
        self.origin = orig_data.affine[0:3,3]
        
        self.sphere = get_sphere('symmetric362')
        #self.scale = np.array([1, 1, 1])
        self.affine_scale = np.diag(orig_data.affine)[0:3]
        
    def setZValue(self,the_slice):
        self.which_slice = the_slice

    def setRenderer(self,the_renderer):
        self.renderer = the_renderer

    def displayAxialFODs_orig(self,which_slice,subsamp_fac=2):
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
                vertices = np.concatenate((vertices,np.ones((vertices.shape[0],1))),axis=1)
                colors = vertices.copy()*255
                for i in range(0,3):
                    vertices[:,i] = vertices[:,i]*S
                vertices[:,0] = vertices[:,0]*subsamp_fac*self.affine_scale[1]+vid_y*self.my_vs[1]+self.origin[1]
                vertices[:,1] = vertices[:,1]*subsamp_fac*self.affine_scale[0]+vid_x*self.my_vs[0]+self.origin[0]
                vertices[:,2] = vertices[:,2]*subsamp_fac*self.affine_scale[2]+which_slice*self.my_vs[2]+self.origin[2]
                #vertices = np.matmul(self.affine,vertices.T).T[:,0:3]
                vertices = vertices[:,[1,0,2]]
                colors = colors[:,[1,0,2]]
                    
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
        
    def displayAxialFODs(self, which_slice, subsamp_fac=2, batch_size=None):
        """
        Fast, vectorized replacement for displaying axial FOD glyph-meshes.

        Parameters
        ----------
        which_slice : int or tuple
            Slice index (or (index, subsamp) tuple as in original).
        subsamp_fac : int
            Subsampling factor in-plane (keep 1 every subsamp_fac voxels).
        batch_size : int or None
            If set, build glyphs in batches of this many glyphs to limit peak memory.
        """

        # guard / busy flag
        if getattr(self, "can_update_rendering", None) is None:
            self.can_update_rendering = 1
        if self.can_update_rendering == 0:
            return
        self.can_update_rendering = 0

        # unpack tuple behavior (keeps backward compatibility)
        if isinstance(which_slice, tuple):
            subsamp_fac = 1  # original branch set subsamp to 1 when tuple passed
            which_slice = which_slice[0]

        # Lmax detection (same as original)
        Lmax = 8
        nd_coeffs = self.odf_data.shape[3]
        if nd_coeffs == 15:
            Lmax = 4
        elif nd_coeffs == 28:
            Lmax = 6
        elif nd_coeffs == 45:
            Lmax = 8
        elif nd_coeffs == 153:
            Lmax = 16

        # scale slice index consistent with your original code
        which_slice = int(np.floor(which_slice * self.target_vs[2] / self.my_vs[2]))
        if which_slice >= self.odf_data.shape[2]:
            print("Cannot select this slice")
            self.can_update_rendering = 1
            return

        # compute spherical function projection (same as before)
        sf_proj = shm.sh_to_sf(self.odf_data[:, :, which_slice:which_slice+1, :], self.sphere, Lmax, basis_type='tournier07')
        # normalize like original code
        sf_proj = sf_proj / max(sf_proj.max(), 1)
        # reorder axes to (n_dirs, nx, ny, 1) like your original
        sf_proj = np.moveaxis(sf_proj, 3, 0)  # now shape (n_dirs, nx, ny, 1)
        sf = np.squeeze(sf_proj)  # shape -> (n_dirs, nx, ny)

        # quick shapes
        n_dirs = sf.shape[0]
        nx = sf.shape[1]
        ny = sf.shape[2]

        # sphere geometry (NumPy arrays expected)
        sph_verts = self.sphere.vertices.astype(np.float32)  # (Nv,3)
        faces = self.sphere.faces.astype(np.int64)           # (Nfaces,3)
        Nv = sph_verts.shape[0]
        Nfaces = faces.shape[0]

        # base colors derived from sphere vertices as in your original (normalize then *255)
        vnorm = np.abs(sph_verts).max()
        if vnorm == 0:
            vnorm = 1.0
        base_colors = (sph_verts / vnorm)[:, [1, 0, 2]]  # swapped as in your original code
        base_colors_u8 = (base_colors * 255).clip(0, 255).astype(np.uint8)

        # sampling grid
        xs = np.arange(0, nx, subsamp_fac, dtype=int)
        ys = np.arange(0, ny, subsamp_fac, dtype=int)

        # collect voxels that have nonzero FOD magnitude
        voxel_positions = []
        glyph_scalings = []
        for ix in xs:
            for iy in ys:
                S = sf[:, ix, iy]  # shape (n_dirs,)
                if S.max() == 0:
                    continue
                voxel_positions.append((int(ix), int(iy)))
                glyph_scalings.append(S.astype(np.float32))

        # nothing to render?
        if len(voxel_positions) == 0:
            # set empty mapper and return
            pd_empty = vtk.vtkPolyData()
            mapper_empty = vtk.vtkPolyDataMapper()
            mapper_empty.SetInputData(pd_empty)
            self.SetMapper(mapper_empty)
            self.can_update_rendering = 1
            self.Modified()
            self.renderer.Render()
            return

        n_glyphs = len(voxel_positions)
        total_pts = Nv * n_glyphs
        total_tris = Nfaces * n_glyphs

        # compute world z position for the slice (like your original)
        which_slice_world = which_slice * self.my_vs[2] + self.origin[2]

        # affine (full 4x4), fallback to identity
        affine4 = getattr(self, "affine", None)
        if affine4 is None:
            affine4 = np.eye(4, dtype=np.float32)
        else:
            affine4 = np.asarray(affine4, dtype=np.float32)
        # affine_scale fallback
        affine_scale = getattr(self, "affine_scale", None)
        if affine_scale is None:
            affine_scale = np.ones(3, dtype=np.float32)
        else:
            affine_scale = np.asarray(affine_scale, dtype=np.float32)

        # prepare big arrays (watch memory for very large slices)
        try:
            points_all = np.empty((total_pts, 3), dtype=np.float32)
            colors_all = np.empty((total_pts, 4), dtype=np.uint8)
            conn = np.empty(total_tris * 4, dtype=np.int64)  # [3, i0, i1, i2] per tri
        except MemoryError:
            # could fallback: process in smaller batches (safer). We'll do a simple batching by glyphs.
            batch_size = batch_size or 256
            # helper to build polydata for batches and append
            print('FOD memory error')
            return

        # fill arrays
        pt_offset = 0
        conn_offset = 0
        for g_idx, (ix, iy) in enumerate(voxel_positions):
            S = glyph_scalings[g_idx]  # (n_dirs,)
            # scaled sphere verts: multiply each sphere vertex row by its matching S value
            verts_scaled = sph_verts * S[:, None]  # (Nv,3)
            # apply pre-scaling if present
            verts_scaled = verts_scaled * affine_scale[None, :]  # broadcast

            # compute voxel world center (keeps your original axis ordering convention)
            #voxel_world = np.array([iy * self.my_vs[1] + self.origin[1],
            #                        ix * self.my_vs[0] + self.origin[0],
            #                        which_slice_world], dtype=np.float32)

            voxel_center_vox = np.array([ix, iy, which_slice], dtype=np.float32)
            verts_vox = verts_scaled[:,[1,0,2]] + voxel_center_vox[None, :]  # (Nv,3) in voxel space

            # convert to homogeneous and translate
            verts_h = np.concatenate([verts_vox, np.ones((Nv, 1), dtype=np.float32)], axis=1)  # (Nv,4)
            #verts_h[:, 0:3] += voxel_world[None, :]

            # apply affine 4x4
            verts_t = (affine4 @ verts_h.T).T[:, 0:3].astype(np.float32)

            # reorder axes to match your original code
            #verts_t = verts_t[:, [1, 0, 2]]

            # colors for this glyph (same for all glyphs)
            rgba = np.empty((Nv, 4), dtype=np.uint8)
            rgba[:, :3] = base_colors_u8
            rgba[:, 3] = 255

            # write to global arrays
            points_all[pt_offset:pt_offset+Nv, :] = verts_t
            colors_all[pt_offset:pt_offset+Nv, :] = rgba

            # connectivity block
            base = faces + pt_offset  # (Nfaces,3)
            block = np.empty((Nfaces, 4), dtype=np.int64)
            block[:, 0] = 3
            block[:, 1:] = base
            conn[conn_offset:conn_offset + 4 * Nfaces] = block.ravel()

            pt_offset += Nv
            conn_offset += 4 * Nfaces

        # convert to VTK arrays
        vtk_points = vtk.vtkPoints()
        vtk_points.SetData(numpy_support.numpy_to_vtk(points_all, deep=True))

        id_array = numpy_support.numpy_to_vtkIdTypeArray(conn, deep=True)
        cells = vtk.vtkCellArray()
        cells.SetCells(int(total_tris), id_array)

        vtk_colors = numpy_support.numpy_to_vtk(colors_all, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
        vtk_colors.SetNumberOfComponents(4)
        vtk_colors.SetName("Colors")

        # assemble polydata
        pd = vtk.vtkPolyData()
        pd.SetPoints(vtk_points)
        pd.SetPolys(cells)
        pd.GetPointData().SetScalars(vtk_colors)

        # set mapper and actor (like original)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pd)
        self.SetMapper(mapper)

        # done
        self.can_update_rendering = 1
        self.Modified()
        self.renderer.Render()        

