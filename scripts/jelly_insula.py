# -*- coding: utf-8 -*-
"""
BNA 岛叶 12 亚区玻璃脑渲染 (brainpy 环境, pyvista 引擎, 全 MNI 空间)
- 玻璃脑: MNI152 1mm T1 等值面 (真实脑壳)
- 岛叶: AAL 岛叶 mask(真实解剖)基准, BNA 12 亚区坐标经尺度对齐后布局
"""
import numpy as np
import nibabel as nib
import pyvista as pv

DATA = r'C:\Users\29698\brain-viz-survey\data'
OUT = r'C:\Users\29698\brain-viz-survey\images'

BNA_INS_VOX = {
    'Ins_L_1': (54,131,105), 'Ins_L_2': (54,118,99), 'Ins_L_3': (53,123,119),
    'Ins_L_4': (56,106,98),  'Ins_L_5': (59,141,122), 'Ins_L_6': (57,143,107),
    'Ins_R_1': (127,107,100),'Ins_R_2': (129,132,104),'Ins_R_3': (127,144,108),
    'Ins_R_4': (131,124,118),'Ins_R_5': (130,120,101),'Ins_R_6': (125,140,122),
}

JELLY_COLORS = [
    '#FF5A5F', '#FFB400', '#38B000', '#00A8A8', '#3A86FF', '#8338EC',
    '#FF7AA2', '#FF9F1C', '#4CC9F0', '#2EC4B6', '#F72585', '#9EF01A',
]


def make_glass_brain():
    """MNI152 1mm -> marching_cubes 等值面 (阈值 150, 2mm 下采样) -> MNI mm mesh"""
    import nibabel as nib
    from skimage.measure import marching_cubes

    t = nib.load(rf'{DATA}\MNI152_T1_1mm_brain.nii')
    data = np.asarray(t.get_fdata(), dtype=np.float32)
    ds = data[::2, ::2, ::2]  # (x,y,z) 2mm 体素
    # skimage marching_cubes: 输入组织为 (x,y,z), 输出 verts 也在该顺序
    verts, faces, _, _ = marching_cubes(ds, level=150, step_size=1)
    # verts 为 (x,y,z) 体素连续坐标 (0..90)
    # 转 MNI mm: affine (放射学: x 翻转)
    mm = verts.copy()
    mm[:, 0] = -mm[:, 0] * 2.0 + 90.0
    mm[:, 1] = mm[:, 1] * 2.0 - 126.0
    mm[:, 2] = mm[:, 2] * 2.0 - 72.0
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    return mesh


def aal_insula_mm():
    """AAL 岛叶 mask 的真实 MNI 坐标 (用于 12 亚区对齐基准)"""
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
    return mm


def register_bna():
    """BNA 12 亚区坐标 -> MNI 岛叶位置 (用左右半球 AAL 岛叶真实中心 + 站点内相对偏移)"""
    aal = aal_insula_mm()
    left = aal[aal[:, 0] < 0]
    right = aal[aal[:, 0] > 0]

    out = {}
    for name, vox in BNA_INS_VOX.items():
        v = np.array(vox, dtype=float)
        ref = left if name.startswith('Ins_L') else right
        rm = ref.mean(axis=0)
        rs = np.array([ref[:, i].std() for i in range(3)])
        # 站点内相对位置: 用全部岛叶 BNA 点做 zscore
        allbna = np.array(list(BNA_INS_VOX.values()), dtype=float)
        bm = allbna.mean(axis=0)
        bs = allbna.std(axis=0)
        vn = (v - bm) / bs
        # y/z 相对岛叶范围幅度, x 用半球符号固定
        x = rm[0] + (0.02 * vn[0] * rs[0])
        y = rm[1] + vn[1] * rs[1] * 0.6
        z = rm[2] + vn[2] * rs[2] * 0.6
        out[name] = np.array([x, y, z])
    return out


def render(alpha_brain=0.10, jelly_alpha=0.65, output='jelly_insula.png',
           add_labels=False, view='front'):
    brain = make_glass_brain()
    pts = register_bna()

    pl = pv.Plotter(off_screen=True, window_size=[1400, 1000])
    pl.set_background('#F7F7F7')
    # 平滑脑表面 (subdivide + smoothing) 消除条纹伪影
    brain_smooth = brain.subdivide(1, subfilter='loop').smooth(n_iter=10,
                                                               relaxation_factor=0.1)
    pl.add_mesh(brain_smooth, color='#4A7DBF', opacity=alpha_brain,
                smooth_shading=True, diffuse=0.5, ambient=0.5,
                specular=0.3, specular_power=64)

    for i, (name, c) in enumerate(pts.items()):
        jelly = pv.Sphere(radius=7.5, center=c, theta_resolution=64, phi_resolution=64)
        pl.add_mesh(jelly, color=JELLY_COLORS[i], opacity=jelly_alpha,
                    smooth_shading=True, specular=0.9, specular_power=128,
                    roughness=0.15, diffuse=0.8, ambient=0.35)
        if add_labels:
            pl.add_point_labels([c], [name], font_size=12, show_points=False,
                                text_color='black')

    # 视角
    if view == 'front':
        pl.camera_position = [(0, -420.0, 10.0), (0, 0, 0), (0, 0, 1)]
    elif view == 'iso':
        pl.camera_position = [(300.0, -300.0, 250.0), (0, 0, 5), (0, 0, 1)]
    elif view == 'top':
        pl.camera_position = [(0, 0, 500.0), (0, 0, 0), (0, 1, 0)]
    pl.reset_camera()
    pl.camera.zoom(1.4)
    pl.screenshot(rf'{OUT}\{output}')
    pl.close()
    return True


if __name__ == '__main__':
    render()
    print('saved')
