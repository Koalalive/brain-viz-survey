# -*- coding: utf-8 -*-
"""jellybrain.core: 玻璃脑 + 果冻亚区渲染引擎.

设计: 一个 AtlasSpec 描述"图谱的某脑区有哪些亚区(名称/中心/网络归属)",
渲染引擎负责 玻璃脑 + 亚区真实形态 (mask->marching cubes->Voronoi 划分)
+ Yeo7 配色 + 图例 + 标签 + 交互式窗口.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Union

import numpy as np

__all__ = [
    "Subregion", "AtlasSpec", "YeoNetwork",
    "make_glass_brain", "voronoi_partition",
    "visualize_subregions", "add_pil_legend",
]


# --------------------------------------------------------------------------
# 数据模型
# --------------------------------------------------------------------------
@dataclass
class Subregion:
    """一个脑区亚区."""
    name: str                       # 短名, 如 "dIa"
    full_name: str                  # 全名, 如 "dorsal agranular"
    mni_center: np.ndarray          # MNI 中心 (mm), 用于 Voronoi
    yeo7: int = 4                   # Yeo-7 网络编号 (1-7), 用于配色


@dataclass
class AtlasSpec:
    """一个"图谱 x 脑区"的可视化规格."""
    atlas_name: str                 # 图谱名, 如 "brainnetome"
    region_name: str                # 脑区名, 如 "insula"
    subregions: List[Subregion]     # 亚区列表
    region_mask_fn: Callable[[], np.ndarray] = None   # -> 3D ROI mask
    region_mask_affine_fn: Callable[[], np.ndarray] = None  # affine 4x4
    color_dir: str = 'yeo7'         # 配色策略: yeo7 / per_subregion
    template: str = 'mni152'        # 玻璃脑模板

    def _default_mask(self):
        raise NotImplementedError


class YeoNetwork:
    """Yeo-7 网络常量 (官方配色)."""
    VISUAL = 1
    SOMATOMOTOR = 2
    DORSAL_ATTENTION = 3
    VENTRAL_ATTENTION = 4
    LIMBIC = 5
    FRONTOPARIETAL = 6
    DEFAULT_MODE = 7

    NAMES = ['Visual', 'Somatomotor', 'Dorsal Attention',
             'Ventral Attention', 'Limbic', 'Frontoparietal',
             'Default Mode']
    RGB = np.array([
        [120, 18, 134], [70, 130, 180], [0, 118, 14],
        [196, 58, 250], [220, 248, 164], [230, 148, 34],
        [205, 62, 78],
    ], dtype=float) / 255.0
    HEX = ['#%02X%02X%02X' % tuple(c) for c in (RGB * 255).astype(int)]


# --------------------------------------------------------------------------
# 玻璃脑
# --------------------------------------------------------------------------
def make_glass_brain(mni152_path: Optional[str] = None,
                     smooth_iter: int = 30) -> "pv.PolyData":
    """MNI152 玻璃脑 (marching cubes + 平滑). 未给路径时用 nilearn 模板."""
    import nibabel as nib
    import pyvista as pv
    from skimage.measure import marching_cubes

    if mni152_path is None:
        from nilearn.datasets import load_mni152_template
        t = load_mni152_template()
    else:
        t = nib.load(mni152_path)
    data = np.asarray(t.get_fdata(), dtype=np.float32)
    # 自适应阈值: 0-1 归一化用 0.5, 0-255 用 150
    level = 0.5 if data.max() <= 2.0 else 150.0
    verts, faces, _, _ = marching_cubes(data, level=level, step_size=1)
    aff = t.affine
    mm = verts.copy()
    # 通用 affine 应用 (含放射学翻转检测): 只处理对角阵
    diag = np.diag(aff)[:3]
    mm[:, 0] = mm[:, 0] * diag[0] + aff[0, 3]
    mm[:, 1] = mm[:, 1] * diag[1] + aff[1, 3]
    mm[:, 2] = mm[:, 2] * diag[2] + aff[2, 3]
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    mesh = mesh.subdivide(1, subfilter='loop').smooth(
        n_iter=smooth_iter, relaxation_factor=0.08)
    return mesh


# --------------------------------------------------------------------------
# 亚区划分
# --------------------------------------------------------------------------
def voronoi_partition(mesh, centers: List[np.ndarray], names: List[str]):
    """把连通 mesh 按最近中心 Voronoi 划分为若干子 mesh."""
    from scipy.spatial import cKDTree
    import pyvista as pv
    tree = cKDTree(np.array(centers))
    _, vert_label = tree.query(mesh.points)
    cells = mesh.faces.reshape(-1, 4)[:, 1:4]
    face_label = np.array([
        np.bincount(vert_label[c], minlength=len(centers)).argmax()
        for c in cells])
    submeshes: Dict[str, "pv.PolyData"] = {}
    for k in range(len(centers)):
        fcells = cells[face_label == k]
        if len(fcells) == 0:
            continue
        uverts = np.unique(fcells)
        mapping = {old: new for new, old in enumerate(uverts)}
        new_faces = np.vectorize(lambda x: mapping[x])(fcells)
        new_mesh = pv.PolyData(
            mesh.points[uverts],
            np.hstack([np.full((new_faces.shape[0], 1), 3),
                       new_faces]).astype(np.int64).ravel())
        submeshes[names[k]] = new_mesh
    return submeshes


def voronoi_boundary_lines(mesh, centers: List[np.ndarray],
                           names: List[str]) -> "pv.PolyData":
    """提取 Voronoi 分区边界边 -> 线段 polyline (用于清晰展示分区边界).

    边界边 = 两个相邻三角面属于不同亚区时所共享的边.
    """
    import pyvista as pv
    from scipy.spatial import cKDTree
    tree = cKDTree(np.array(centers))
    _, vert_label = tree.query(mesh.points)
    cells = mesh.faces.reshape(-1, 4)[:, 1:4]
    face_label = np.array([
        np.bincount(vert_label[c], minlength=len(centers)).argmax()
        for c in cells])

    # 边 -> 两个面的 label
    edge_faces: Dict[tuple, list] = {}
    for ci, fc in enumerate(cells):
        for a, b in [(fc[0], fc[1]), (fc[1], fc[2]), (fc[2], fc[0])]:
            key = (min(a, b), max(a, b))
            edge_faces.setdefault(key, []).append(face_label[ci])

    # 边界边 (相邻面 label 不同)
    boundary = []
    for (a, b), labels in edge_faces.items():
        if len(set(labels)) > 1:
            boundary.append((a, b))

    lines = []
    for a, b in boundary:
        lines.append([a, b])
    if lines:
        cells = np.hstack([np.array([2] * len(lines))[:, None],
                           np.array(lines)]).astype(np.int64).ravel()
    else:
        cells = np.array([2, 0, 1], dtype=np.int64)
    line_mesh = pv.PolyData(mesh.points, lines=cells)  # 线布局 [2,a,b]
    return line_mesh


def region_surface(spec: AtlasSpec, smooth_sigma: float = 1.5,
                   subdivide: int = 4, smooth_iter: int = 60):
    """脑区真实形态表面 (mask -> marching cubes -> 平滑)."""
    import nibabel as nib
    import pyvista as pv
    from skimage.measure import marching_cubes
    from scipy.ndimage import gaussian_filter

    mask = spec.region_mask_fn()
    vol = gaussian_filter(mask.astype(np.float32), sigma=smooth_sigma)
    pad = 6
    volp = np.pad(vol, pad, mode='constant')
    verts, faces, _, _ = marching_cubes(volp, level=0.5, step_size=1)
    verts = verts - pad
    aff = spec.region_mask_affine_fn()
    mm = (aff[:3, :3] @ verts.T).T + aff[:3, 3]
    mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                      faces]).astype(np.int64).ravel())
    # 细分 + 平滑 (更多轮 -> 更光滑)
    mesh = mesh.subdivide(subdivide, subfilter='loop').smooth(
        n_iter=smooth_iter, relaxation_factor=0.05)
    return mesh


# --------------------------------------------------------------------------
# 主渲染
# --------------------------------------------------------------------------
def visualize_subregions(
    spec: AtlasSpec,
    output: Optional[str] = None,
    view: str = 'iso',
    add_labels: bool = True,
    show_legend: bool = True,
    show_boundaries: bool = True,
    boundary_color: str = '#333333',
    boundary_radius: float = 0.5,
    label_offsets: Optional[Dict[str, np.ndarray]] = None,
    alpha_brain: float = 0.06,
    alpha_region: float = 0.5,
    return_plotter: bool = False,
    mni152_path: Optional[str] = None,
    camera_zoom: float = 1.35,
):
    """渲染玻璃脑 + 亚区果冻. 返回 None / 保存图片 / 或 plotter (交互)."""
    import pyvista as pv
    from PIL import Image

    brain = make_glass_brain(mni152_path)
    surf = region_surface(spec)
    centers = [s.mni_center for s in spec.subregions]
    names = [s.name for s in spec.subregions]
    sub = voronoi_partition(surf, centers, names)

    pl = pv.Plotter(off_screen=(not return_plotter), window_size=[1600, 1100])
    pl.set_background('#EDF2F8')

    # ---------------- 光照设置 (PBR) ----------------
    pl.enable_anti_aliasing('ssaa')
    pl.remove_all_lights()  # 移除默认灯光, 手动加
    for pos, intens, color in [
        ((1, 1, 1), 1.2, (1.0, 1.0, 1.0)),      # 主光
        ((-1, -0.5, 0.5), 0.5, (0.9, 0.95, 1.0)),  # 补光
        ((0, 0, 1), 0.4, (0.85, 0.9, 1.0)),     # 顶光
    ]:
        pl.add_light(pv.Light(position=pos, light_type='camera light',
                              intensity=intens, color=color))

    # ---------------- 玻璃脑 (更清澈, 加菲涅尔感) ----------------
    pl.add_mesh(brain, color='#5A8FC7', opacity=alpha_brain,
                smooth_shading=True, diffuse=0.6, ambient=0.35,
                specular=0.8, specular_power=128, metallic=0.0,
                roughness=0.1, show_edges=False)

    # ---------------- 岛叶亚区 (PBR 果冻) ----------------
    for s in spec.subregions:
        sm = sub.get(s.name)
        if sm is None:
            continue
        if spec.color_dir == 'yeo7':
            rgb = YeoNetwork.RGB[s.yeo7 - 1]
        else:
            rgb = None
        # 亮度增强 + 饱和度提升 (PBR)
        r, g, b = (rgb if rgb is not None else (0.7, 0.7, 0.7))
        r = min(1.0, r * 1.25 + 0.05)
        g = min(1.0, g * 1.25 + 0.05)
        b = min(1.0, b * 1.25 + 0.05)
        pl.add_mesh(sm, color=(r, g, b), opacity=alpha_region,
                    smooth_shading=True, specular=1.0, specular_power=128,
                    roughness=0.1, metallic=0.05, diffuse=0.9, ambient=0.35,
                    show_edges=False, lighting=True)

    # ---------------- 分区边界线 (深灰 tube, 清晰展示亚区分界) ----------------
    if show_boundaries:
        bnd = voronoi_boundary_lines(surf, centers, names)
        bnd = bnd.tube(radius=boundary_radius)  # 实体管, 不被半透明面遮挡
        pl.add_mesh(bnd, color=boundary_color,
                    smooth_shading=True, lighting=False, pickable=False,
                    opacity=0.98)

    # ---------------- 地面阴影 ----------------
    try:
        pl.enable_shadows()
    except Exception:
        pass

    # 视角
    if view == 'front':
        pl.camera_position = [(0, -400.0, 10.0), (0, 0, 0), (0, 0, 1)]
    elif view == 'iso':
        pl.camera_position = [(280.0, -280.0, 240.0), (0, 0, 5), (0, 0, 1)]
    elif view == 'top':
        pl.camera_position = [(0, 0, 500.0), (0, 0, 0), (0, 1, 0)]
    pl.reset_camera()
    pl.camera.zoom(camera_zoom)

    if return_plotter:
        # 交互/HTML 模式保留 3D 标签 (用户可旋转); label_offsets 自定义锚点
        if add_labels:
            for s in spec.subregions:
                sm = sub.get(s.name)
                if sm is None:
                    continue
                anchor = np.array(sm.center, dtype=float)
                if label_offsets and s.name in label_offsets:
                    anchor = anchor + np.asarray(label_offsets[s.name], dtype=float)
                pl.add_point_labels(
                    [anchor], [s.full_name], font_size=14,
                    show_points=False, text_color='#202020',
                    shape_color='#FFFFFF', shape_opacity=0.95,
                    always_visible=True)
        return pl

    pl.screenshot(output)
    pl.close()
    if show_legend:
        add_pil_legend(output, YeoNetwork.NAMES, YeoNetwork.HEX,
                       title='Yeo-7 Networks')
    if add_labels:
        pil_subregion_labels(output, doc=spec, camera_side=view,
                             label_offsets=label_offsets)
    return True


def export_pdf(png_path: str, pdf_path: str):
    """把渲染的 PNG 转成 PDF (多页可追加)."""
    from PIL import Image
    img = Image.open(png_path).convert('RGB')
    img.save(pdf_path, 'PDF', resolution=150.0)
    return pdf_path


def pil_subregion_labels(img_path: str, doc: 'AtlasSpec',
                         camera_side: str = 'iso',
                         label_offsets: Optional[Dict[str, np.ndarray]] = None):
    """用亚区 MNI 中心投影到 2D, 贪心放置不重叠标签 (白底+引线).

    label_offsets: {subregion_name: (dx, dy) 屏幕像素偏移} 自定义标签位置.
    """
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(img_path).convert('RGB')
    w, h = img.size
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 15)
    except Exception:
        font = ImageFont.load_default()

    # 亚区中心 -> 2D 屏幕坐标: 使用与渲染相机一致的等距投影
    # iso 相机: pos=(280,-280,240), 焦点 (0,0,5) => 视线 v=(−280,280,−235)
    # 投影: 右轴 u = normalize(cross(up,v)), 上轴 = cross(v,u)
    if camera_side == 'front':
        pos = np.array([0.0, -400.0, 10.0]); focus = np.array([0.0, 0.0, 0.0])
    elif camera_side == 'top':
        pos = np.array([0.0, 0.0, 500.0]); focus = np.array([0.0, 0.0, 0.0])
    else:
        pos = np.array([280.0, -280.0, 240.0]); focus = np.array([0.0, 0.0, 5.0])
    up = np.array([0.0, 0.0, 1.0]) if camera_side != 'top' else np.array([0.0, 1.0, 0.0])
    v = (focus - pos); v /= np.linalg.norm(v)
    u = np.cross(up, v); u /= np.linalg.norm(u)
    uu = np.cross(v, u)
    scale = 2.6  # 视野半径

    anchors = []
    for s in doc.subregions:
        c = s.mni_center.astype(float)
        d = c - pos
        sx = w / 2 + np.dot(d, u) * scale * 6
        sy = h / 2 - np.dot(d, uu) * scale * 6
        # 自定义标签位置偏移 (屏幕像素)
        if label_offsets and s.name in label_offsets:
            off = np.asarray(label_offsets[s.name], dtype=float)
            sx += float(off[0])
            sy += float(off[1])
        anchors.append((float(sx), float(sy), s.name, s.full_name))

    placed = []
    for sx, sy, name, full in anchors:
        tw = draw.textlength(full, font=font)
        th = 26
        lx, ly = sx + 10, sy - th / 2
        tries = 0
        while any(abs(lx - px) < tw + 14 and abs(ly - py) < th + 10
                  for px, py, *_ in placed):
            lx += 18
            ly += 16
            tries += 1
            if tries > 50:
                break
        placed.append((lx, ly, tw, th))
        rgb = YeoNetwork.RGB[s.yeo7 - 1]
        hexc = '#%02X%02X%02X' % tuple(int(v * 255) for v in rgb)
        # 文字底框 (含 padding, 防裁切)
        draw.rounded_rectangle([lx - 4, ly - 4, lx + tw + 14, ly + th + 4],
                               radius=5, fill=(255, 255, 255, 210),
                               outline=(80, 80, 80), width=1)
        draw.rounded_rectangle([lx - 4, ly, lx + 12, ly + th - 2],
                               radius=2, fill=hexc)
        draw.text((lx + 16, ly + 2), full, fill=(30, 30, 30), font=font)
        # 引线: 从标签框左边缘 -> 锚点 (避开框体)
        draw.line([(lx - 4, ly + th / 2), (sx, sy)],
                  fill=(90, 90, 90), width=1)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=hexc)

    img.save(img_path)
    return True


def add_pil_legend(img_path: str, names: Sequence[str], hexes: Sequence[str],
                   title: str = 'Yeo-7 Networks'):
    """PIL 右下角叠加图例."""
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
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=10,
                         fill=(255, 255, 255, 215), outline=(0, 0, 0, 60),
                         width=2)
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
