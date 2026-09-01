# -*- coding: utf-8 -*-
"""诊断玻璃脑等值面空间范围。"""
import numpy as np
import nibabel as nib
import pyvista as pv

t = nib.load(r'C:\Users\29698\brain-viz-survey\data\MNI152_T1_1mm_brain.nii')
data = np.asarray(t.get_fdata(), dtype=np.float32)
ds = data[::2, ::2, ::2]
print('ds shape (x,y,z):', ds.shape)

# pyvista ImageData: spacing 沿 (x,y,z), data 排列顺序为 x 最快 (Fortran)
vti = pv.ImageData(dimensions=ds.shape, spacing=[2, 2, 2], origin=[0, 0, 0])
# point_data 期望长度 = nx*ny*nz, 按 x 变化最快
vti.point_data['raw'] = np.ascontiguousarray(ds.ravel(order='F'))
mesh = vti.contour([150])
print('mesh bounds (voxel):', mesh.bounds)
pts = np.array(mesh.points)
print('npts:', pts.shape)
# 转换: affine 应用到体素 -> mm
aff = t.affine
# 体素连续坐标 (x*2+0), 用真实 affine 的缩放再平移:
mm = pts.copy()
mm[:, 0] = 2 * pts[:, 0] * aff[0, 0] + aff[0, 3]   # -2x + 90
mm[:, 1] = 2 * pts[:, 1] * aff[1, 1] + aff[1, 3]   # 2y - 126
mm[:, 2] = 2 * pts[:, 2] * aff[2, 2] + aff[2, 3]   # 2z - 72
print('mm x:', mm[:,0].min(), mm[:,0].max())
print('mm y:', mm[:,1].min(), mm[:,1].max())
print('mm z:', mm[:,2].min(), mm[:,2].max())
# 岛叶应在 x -48..48; y -30..30; z -20..25 左右
