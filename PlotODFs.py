
import vtk
import numpy as np
from pymatreader import read_mat
from fury import utils
from dipy.data import get_sphere, get_fnames
import dipy.reconst.shm as shm
import nibabel 

sphere = get_sphere('symmetric362')

renWin = vtk.vtkRenderWindow()
renderer = vtk.vtkRenderer()
window_size = 1024

scale = 3;

# sphere.vertices[:,0] = sphere.vertices[:,0]/sphere.vertices[:,0].max();
# sphere.vertices[:,1] = sphere.vertices[:,1]/sphere.vertices[:,1].max();
# sphere.vertices[:,2] = sphere.vertices[:,2]/sphere.vertices[:,2].max();

my_odfs = nibabel.load('SS_CSD_DIPY.nii');
my_odfs = my_odfs.get_data()[:,:,172:173,:];

my_odf = shm.sh_to_sf(my_odfs,sphere,8)
my_odf = my_odf/my_odf.max();
master_actor = vtk.vtkAppendPolyData()

for vid_x in np.arange(0,my_odf.shape[0],2):#range(0,my_odf.shape[0]):
    for vid_y in np.arange(0,my_odf.shape[1],2):
        odf_pdata = vtk.vtkPolyData()
        vertices = sphere.vertices.copy();
        for i in range(0,3):
            vertices[:,i] = vertices[:,i]*scale*my_odf[vid_x,vid_y,0,:].flatten()        
        vertices[:,0] = vertices[:,0]+vid_x;
        vertices[:,1] = vertices[:,1]+vid_y;
            
        utils.set_polydata_vertices(odf_pdata,vertices);
        utils.set_polydata_triangles(odf_pdata,sphere.faces);
        colors = vertices*255;
        utils.set_polydata_colors(odf_pdata,colors);
        
        master_actor.AddInputData(odf_pdata)

# odf_actor = utils.get_actor_from_polydata(master_actor);#vtk.vtkRenderer()
cleanFilter = vtk.vtkCleanPolyData()
cleanFilter.SetInputConnection(master_actor.GetOutputPort())
mapper = vtk.vtkPolyDataMapper();
mapper.SetInputConnection(cleanFilter.GetOutputPort())

odf_actor = vtk.vtkActor()
odf_actor.SetMapper(mapper)

renderer.AddActor(odf_actor);
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
