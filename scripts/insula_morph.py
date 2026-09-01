# -*- coding: utf-8 -*-
"""
BNA 岛叶 12 亚区形态渲染 v2 (brainpy env, pyvista)
- 更平滑: 1mm marching cubes + 多轮平滑
- 材质按 Yeo-7 网络区分 (每个岛叶亚区归属 Yeo 网络, 用对应网络色)
- 图例: Yeo-7 色卡 (可开关)
- 交互: trame backend + HTML 导出
"""
import numpy as np
import nibabel as nib
import pyvista as pv
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter

DATA = r'C:\Users\29698\brain-viz-survey\data'
OUT = r'C:\Users\29698\brain-viz-survey\images'

# BNA 岛叶 12 亚区体素坐标
BNA_INS_VOX = {
    'Ins_L_1': (54,131,105), 'Ins_L_2': (54,118,99), 'Ins_L_3': (53,123,119),
    'Ins_L_4': (56,106,98),  'Ins_L_5': (59,141,122), 'Ins_L_6': (57,143,107),
    'Ins_R_1': (127,107,100),'Ins_R_2': (129,132,104),'Ins_R_3': (127,144,108),
    'Ins_R_4': (131,124,118),'Ins_R_5': (130,120,101),'Ins_R_6': (125,140,122),
}

# Yeo-7 网络 (名称 + 官方 RGB)
YEO_7 = [
    ('Visual',            (120, 18, 134)),
    ('Somatomotor',       (70, 130, 180)),
    ('Dorsal Attention',  (0, 118, 14)),
    ('Ventral Attention', (196, 58, 250)),
    ('Limbic',            (220, 248, 164)),
    ('Frontoparietal',    (230, 148, 34)),
    ('Default Mode',      (205, 62, 78)),
]
YEO_NAMES = [n for n, _ in YEO_7]
YEO_RGB = np.array([c for _, c in YEO_7], dtype=np.float64) / 255.0
YEO_HEX = ['#%02X%02X%02X' % tuple(c) for _, c in YEO_7]


def make_glass_brain(smooth=True):
    """MNI152 1mm -> 1mm 等值面 + 多轮平滑 (玻璃脑)"""
    from skimage.measure import marching_cubes
    t = nib.load(rf'{DATA}\MNI152_T1_1mm_brain.nii')
    data = np.asarray(t.get_fdata(), dtype=np.float32)
    verts, faces, _, _ = marching_cubes(data, level=150, step_size=1)
    mm = verts.copy()
    mm[:, 0] = -mm[:, 0] + 90.0
    mm[:, 1] = mm[:, 1] - 126.0
    mm[:, 2] = mm[:, 2] - 72.0
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    if smooth:
        mesh = mesh.subdivide(1, subfilter='loop').smooth(
            n_iter=30, relaxation_factor=0.08)
    return mesh


def get_insula_mask_and_aff():
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


def make_insulacortex(smooth_h=1.2):
    """真实岛叶形态 (更平滑: 更高 sigma + 细分平滑)"""
    from skimage.measure import marching_cubes
    mask, img = get_insula_mask_and_aff()
    vol = gaussian_filter(mask.astype(np.float32), sigma=smooth_h)
    pad = 6
    volp = np.pad(vol, pad, mode='constant')
    verts, faces, _, _ = marching_cubes(volp, level=0.5, step_size=1)
    verts = verts - pad
    aff = img.affine
    mm = (aff[:3, :3] @ verts.T).T + aff[:3, 3]
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    # 平滑: 细分 2 次 + laplacian 平滑
    mesh = mesh.subdivide(2, subfilter='loop').smooth(
        n_iter=40, relaxation_factor=0.06)
    return mesh


def bna_centers_mni():
    """12 亚区中心 -> MNI mm"""
    from nilearn import image, datasets
    a = datasets.fetch_atlas_aal(version='SPM12')
    img = image.load_img(a['maps'])
    data = np.asarray(img.get_fdata())
    labels = a['labels']
    idxs = a['indices']
    mask = np.zeros_like(data, dtype=bool)
    for i, n in enumerate(labels):
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


def sample_yeo_network(submeshes):
    """每个亚区 mesh 顶点 -> Yeo-7 投票 (多数网络)"""
    from nilearn import datasets
    import nibabel as nib
    y = datasets.fetch_atlas_yeo_2011('7Networks')
    img = nib.load(y['thick_7'])
    data = np.asarray(img.get_fdata()[..., 0])
    aff = img.affine
    inv = np.linalg.inv(aff)

    nets = {}
    for name, sm in submeshes.items():
        # 采样该亚区顶点
        pts = sm.points
        from collections import Counter
        cnt = Counter()
        for c in pts[::3]:  # 每 3 个顶点采样
            vox = inv @ np.array([c[0], c[1], c[2], 1.0])
            xi = int(np.clip(round(vox[0]), 0, data.shape[0]-1))
            yi = int(np.clip(round(vox[1]), 0, data.shape[1]-1))
            zi = int(np.clip(round(vox[2]), 0, data.shape[2]-1))
            lab = int(data[xi, yi, zi])
            if lab > 0:
                cnt[lab] += 1
        if cnt:
            nets[name] = cnt.most_common(1)[0][0]
        else:
            nets[name] = 4  # 默认 Ventral Attention
    return nets


def voronoi_partition(mesh, centers, names):
    tree = cKDTree(centers)
    centers = np.array(centers)
    _, vert_label = tree.query(mesh.points)
    cells = mesh.faces.reshape(-1, 4)[:, 1:4]
    face_label = np.array([np.bincount(vert_label[c], minlength=len(centers)).argmax()
                           for c in cells])
    submeshes = {}
    for k in range(len(centers)):
        fcells = cells[face_label == k]
        if len(fcells) == 0:
            continue
        uverts = np.unique(fcells)
        mapping = {old: new for new, old in enumerate(uverts)}
        new_faces = np.vectorize(lambda x: mapping[x])(fcells)
        new_mesh = pv.PolyData(mesh.points[uverts],
                               np.hstack([np.full((new_faces.shape[0], 1), 3),
                                          new_faces]).astype(np.int64).ravel())
        submeshes[names[k]] = new_mesh
    return submeshes


def render_morph(output='insula_morph_iso.png', view='iso', add_labels=True,
                 alpha_brain=0.06, alpha_insula=0.5, show_legend=True,
                 return_plotter=False):
    brain = make_glass_brain()
    insula = make_insulacortex()
    centers = bna_centers_mni()
    names = list(centers.keys())
    sub = voronoi_partition(insula, [centers[n] for n in names], names)
    nets = sample_yeo_network(sub)

    pl = pv.Plotter(off_screen=(not return_plotter), window_size=[1600, 1100])
    pl.set_background('#F7F7F7')
    pl.add_mesh(brain, color='#4A7DBF', opacity=alpha_brain,
                smooth_shading=True, diffuse=0.5, ambient=0.5,
                specular=0.3, specular_power=64)

    # 每个亚区用 Yeo 网络色
    for i, (name, sm) in enumerate(sub.items()):
        net = nets[name]
        rgb = YEO_RGB[net-1]
        pl.add_mesh(sm, color=tuple(rgb), opacity=alpha_insula,
                    smooth_shading=True, specular=1.0, specular_power=128,
                    roughness=0.08, diffuse=0.9, ambient=0.3)
        if add_labels:
            pl.add_point_labels([sm.center], [name], font_size=16,
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

    # Yeo-7 图例: 渲染后用 PIL 叠加 (避免 VTK legend 渲染问题)
    pl.reset_camera()
    pl.camera.zoom(1.35)

    if return_plotter:
        return pl
    pl.screenshot(rf'{OUT}\{output}')
    pl.close()
    if show_legend:
        add_pil_legend(rf'{OUT}\{output}', YEO_NAMES, YEO_HEX)
    return True


def add_pil_legend(img_path, names, hexes, title='Yeo-7 Networks'):
    """用 PIL 在图片右下角叠加图例 (色块 + 网络名)"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(img_path).convert('RGB')
    w, h = img.size
    pad = 14
    rows = len(names)
    box_w = 300
    row_h = 34
    box_h = 44 + rows * row_h
    x0 = w - box_w - 30
    y0 = h - box_h - 30

    draw = ImageDraw.Draw(img)
    # 半透明背景
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=10,
                         fill=(255, 255, 255, 215), outline=(0, 0, 0, 60), width=2)
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('arial.ttf', 16)
        fontt = ImageFont.truetype('arial.ttf', 18)
    except Exception:
        font = ImageFont.load_default()
        fontt = font

    draw.text((x0 + 16, y0 + 12), title, fill=(30, 30, 30), font=fontt)
    for i, (nm, hx) in enumerate(zip(names, hexes)):
        yy = y0 + 46 + i * row_h
        draw.rounded_rectangle([x0 + 16, yy, x0 + 46, yy + 22], radius=5,
                               fill=hx, outline=(0, 0, 0, 80), width=1)
        draw.text((x0 + 58, yy + 1), nm, fill=(40, 40, 40), font=font)
    img.convert('RGB').save(img_path)
    return True


def render_interactive(write_html=True):
    """交互式窗口 (trame backend), 可选导出 HTML"""
    pl = render_morph(return_plotter=True)
    if write_html:
        try:
            pl.export_html(rf'{OUT}\insula_interactive.html')
            print('HTML exported')
        except Exception as e:
            print('HTML export failed:', e)
    pl.show(jupyter_backend='trame', interactive=True)
    return pl


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        render_interactive()
    else:
        render_morph(output='insula_morph_iso.png', view='iso')
        print('saved')
