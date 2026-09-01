# -*- coding: utf-8 -*-
"""
BNA 岛叶 12 亚区形态渲染 (brainpy 环境, pyvista)
- 玻璃脑: MNI152 等值面 + 平滑
- 岛叶: AAL 岛叶 mask marching_cubes 提取真实沟回形态 -> 按 BNA 12 亚区中心 Voronoi 划分着色
"""
import numpy as np
import nibabel as nib
import pyvista as pv
from scipy.spatial import cKDTree

DATA = r'C:\Users\29698\brain-viz-survey\data'
OUT = r'C:\Users\29698\brain-viz-survey\images'

# BNA 岛叶 12 亚区体素坐标 (站点坐标)
BNA_INS_VOX = {
    'Ins_L_1': (54,131,105), 'Ins_L_2': (54,118,99), 'Ins_L_3': (53,123,119),
    'Ins_L_4': (56,106,98),  'Ins_L_5': (59,141,122), 'Ins_L_6': (57,143,107),
    'Ins_R_1': (127,107,100),'Ins_R_2': (129,132,104),'Ins_R_3': (127,144,108),
    'Ins_R_4': (131,124,118),'Ins_R_5': (130,120,101),'Ins_R_6': (125,140,122),
}

# 果冻色卡: 左右同名同色, 相邻编号高对比 (INS-1红 INS-2蓝 INS-3绿 INS-4紫 INS-5橙 INS-6青)
JELLY_COLORS = [
    '#FF3B30', '#007AFF', '#34C759', '#AF52DE', '#FF9500', '#00C7BE',
    '#FF3B30', '#007AFF', '#34C759', '#AF52DE', '#FF9500', '#00C7BE',
]


def make_glass_brain():
    """MNI152 -> 等值面 + 平滑"""
    from skimage.measure import marching_cubes
    t = nib.load(rf'{DATA}\MNI152_T1_1mm_brain.nii')
    data = np.asarray(t.get_fdata(), dtype=np.float32)
    ds = data[::2, ::2, ::2]
    verts, faces, _, _ = marching_cubes(ds, level=150, step_size=1)
    mm = verts.copy()
    mm[:, 0] = -mm[:, 0] * 2.0 + 90.0
    mm[:, 1] = mm[:, 1] * 2.0 - 126.0
    mm[:, 2] = mm[:, 2] * 2.0 - 72.0
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    return mesh


def get_insula_mask_and_aff():
    """获取 AAL 岛叶 mask + affine"""
    from nilearn import image, datasets
    a = datasets.fetch_atlas_aal(version='SPM12')
    img = image.load_img(a['maps'])
    data = np.asarray(img.get_fdata())
    names = a['labels']
    idxs = a['indices']
    mask = np.zeros_like(data, dtype=bool)
    for i, n in enumerate(names):
        if 'Insula' in str(n):
            mask |= (np.round(data) == float(idxs[i]))
    return mask, img


def make_insulacortex():
    """从 AAL 岛叶 mask 提取真实岛叶 3D 表面 (MNI mm)"""
    from skimage.measure import marching_cubes
    mask, img = get_insula_mask_and_aff()
    data = np.asarray(img.get_fdata())
    # 平滑 mask 产生更光滑表面
    from scipy.ndimage import gaussian_filter
    vol = gaussian_filter(mask.astype(np.float32), sigma=0.7)
    # 需要 padding (岛叶在边缘可能缺)
    pad = 5
    volp = np.pad(vol, pad, mode='constant')
    verts, faces, _, _ = marching_cubes(volp, level=0.5, step_size=1)
    verts = verts - pad
    aff = img.affine
    mm = (aff[:3, :3] @ verts.T).T + aff[:3, 3]
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    return mesh


def bna_centers_mni():
    """12 亚区中心 -> MNI mm (标准对齐: 左右半球中心 + 相对 y/z)"""
    from nilearn import image, datasets
    a = datasets.fetch_atlas_aal(version='SPM12')
    img = image.load_img(a['maps'])
    data = np.asarray(img.get_fdata())
    names = a['labels']
    idxs = a['indices']
    mask = np.zeros_like(data, dtype=bool)
    for i, n in enumerate(names):
        if 'Insula' in str(n):
            mask |= (np.round(data) == float(idxs[i]))
    coords = np.argwhere(mask)
    aff = img.affine
    mm = (aff[:3, :3] @ coords.T).T + aff[:3, 3]
    left = mm[mm[:, 0] < 0]
    right = mm[mm[:, 0] > 0]

    allb = np.array(list(BNA_INS_VOX.values()), dtype=float)
    bm = allb.mean(axis=0)
    bs = allb.std(axis=0)

    out = {}
    for name, vox in BNA_INS_VOX.items():
        v = np.array(vox, dtype=float)
        ref = left if name.startswith('Ins_L') else right
        rm = ref.mean(axis=0)
        rs = np.array([ref[:, i].std() for i in range(3)])
        vn = (v - bm) / bs
        x = rm[0] + vn[0] * rs[0] * 0.02
        y = rm[1] + vn[1] * rs[1] * 0.6
        z = rm[2] + vn[2] * rs[2] * 0.6
        out[name] = np.array([x, y, z])
    return out


def voronoi_partition(mesh, centers, names):
    """用亚区中心把岛叶表面顶点划分到最近亚区, 返回每亚区的面"""
    tree = cKDTree(centers)
    centers = np.array(centers)
    # 顶点归属
    _, vert_label = tree.query(mesh.points)
    cells = mesh.faces.reshape(-1, 4)[:, 1:4]
    # 每面的归属 = 面顶点多数
    face_label = np.array([np.bincount(vert_label[c], minlength=len(centers)).argmax()
                           for c in cells])
    submeshes = {}
    for k in range(len(centers)):
        fcells = cells[face_label == k]
        if len(fcells) == 0:
            continue
        # 收集用到的顶点
        uverts = np.unique(fcells)
        mapping = {old: new for new, old in enumerate(uverts)}
        new_faces = np.vectorize(lambda x: mapping[x])(fcells)
        new_mesh = pv.PolyData(mesh.points[uverts],
                               np.hstack([np.full((new_faces.shape[0], 1), 3),
                                          new_faces]).astype(np.int64).ravel())
        submeshes[names[k]] = new_mesh
    return submeshes


def render_morph(alpha_brain=0.10, alpha_insula=0.55, output='insula_morph.png',
                 view='iso', add_labels=False):
    brain = make_glass_brain()
    insula = make_insulacortex()
    centers = bna_centers_mni()
    names = list(centers.keys())
    cents = np.array([centers[n] for n in names])
    submeshes = voronoi_partition(insula, cents, names)

    pl = pv.Plotter(off_screen=True, window_size=[1400, 1100])
    pl.set_background('#F7F7F7')
    # 玻璃脑 (半透明平滑)
    b = brain.subdivide(1, subfilter='loop').smooth(n_iter=10, relaxation_factor=0.1)
    pl.add_mesh(b, color='#4A7DBF', opacity=alpha_brain,
                smooth_shading=True, diffuse=0.5, ambient=0.5,
                specular=0.3, specular_power=64)

    # 岛叶各亚区 (真实形态, 果冻质感)
    for i, (name, sm) in enumerate(submeshes.items()):
        pl.add_mesh(sm, color=JELLY_COLORS[i], opacity=alpha_insula,
                    smooth_shading=True, specular=1.0, specular_power=128,
                    roughness=0.08, diffuse=0.9, ambient=0.3)
        if add_labels:
            pl.add_point_labels([sm.center], [name], font_size=18,
                                show_points=False, text_color='#FFFFFF',
                                shape_color='#333333', shape_opacity=0.85,
                                always_visible=True)

    # 视角
    if view == 'front':
        pl.camera_position = [(0, -400.0, 10.0), (0, 0, 0), (0, 0, 1)]
    elif view == 'iso':
        pl.camera_position = [(280.0, -280.0, 240.0), (0, 0, 5), (0, 0, 1)]
    elif view == 'top':
        pl.camera_position = [(0, 0, 500.0), (0, 0, 0), (0, 1, 0)]
    pl.reset_camera()
    pl.camera.zoom(1.35)
    pl.screenshot(rf'{OUT}\{output}')
    pl.close()
    return True


if __name__ == '__main__':
    render_morph(output='insula_morph_iso.png', view='iso')
    print('saved')
