# -*- coding: utf-8 -*-
"""解析 MNI obj -> pyvista mesh。"""
import numpy as np
import pyvista as pv

verts = []
faces = []
with open(r'C:\Users\29698\brain-viz-survey\data\surf_reg_model.obj') as f:
    lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]

for l in lines[1:]:
    parts = l.split()
    if len(parts) == 3:
        verts.append([float(x) for x in parts])
    elif len(parts) == 8:
        idx = [int(x) for x in parts]
        for j in range(0, 6, 3):
            faces.append([idx[j], idx[j+1], idx[j+2]])

verts = np.array(verts)
faces = np.array(faces)
print('verts', verts.shape, 'faces', faces.shape)
print('x', verts[:,0].min(), verts[:,0].max())
print('y', verts[:,1].min(), verts[:,1].max())
print('z', verts[:,2].min(), verts[:,2].max())

mesh = pv.PolyData(verts, np.hstack([np.full((faces.shape[0],1), 3), faces]).astype(np.int64).ravel())
print('mesh', mesh.n_points, mesh.n_cells)
mesh.save(r'C:\Users\29698\brain-viz-survey\data\mni_surface.vtk')
print('saved')
