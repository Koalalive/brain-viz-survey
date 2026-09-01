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
    name: str                       # 唯一名, 如 "Ins_L_1"
    full_name: str                  # 全名, 如 "G · hypergranular"
    mni_center: np.ndarray          # MNI 中心 (mm), 用于 Voronoi
    yeo7: int = 4                   # Yeo-7 网络编号 (1-7), 用于配色
    short: str = ''                 # 脑区名, 如 "G"/"dIa" (标签用)


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


# 12 亚区独立配色 (每亚区一色, 高区分度)
SUBR_COLORS = [
    '#FF3B30', '#FF9500', '#FFCC00', '#34C759', '#00C7BE', '#007AFF',
    '#AF52DE', '#FF2D55', '#5AC8FA', '#30B0C7', '#A2845E', '#88D600',
]


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


def dashed_boundary_lines(mesh, centers: List[np.ndarray],
                          names: List[str],
                          dash_ratio: float = 0.55,
                          n_segments: int = 5,
                          lift: float = 0.6) -> "pv.PolyData":
    """提取亚区分界并生成**虚线** (隔段交替保留), 浅色细线.

    dash_ratio: 每段实线占比; n_segments: 每条边细分段数;
    lift: 沿法线抬升 (mm), 让虚线浮于半透明亚区表面之上可见.
    """
    import pyvista as pv
    from scipy.spatial import cKDTree
    tree = cKDTree(np.array(centers))
    _, vert_label = tree.query(mesh.points)
    cells = mesh.faces.reshape(-1, 4)[:, 1:4]
    face_label = np.array([
        np.bincount(vert_label[c], minlength=len(centers)).argmax()
        for c in cells])

    # 顶点法线 (抬升用)
    normals = np.asarray(mesh.compute_normals(cell_normals=False,
                                              split_vertices=False)
                         .point_data['Normals'], dtype=float)

    edge_faces: Dict[tuple, list] = {}
    for ci, fc in enumerate(cells):
        for a, b in [(fc[0], fc[1]), (fc[1], fc[2]), (fc[2], fc[0])]:
            key = (min(a, b), max(a, b))
            edge_faces.setdefault(key, []).append(face_label[ci])

    pts = np.asarray(mesh.points, dtype=float)
    dash_lines = []
    for (a, b), labels in edge_faces.items():
        if len(set(labels)) > 1:
            pa = pts[a] + normals[a] * lift
            pb = pts[b] + normals[b] * lift
            for k in range(n_segments):
                t0 = k / n_segments
                t1 = t0 + dash_ratio / n_segments
                if k % 2 == 0:
                    dash_lines.append((pa + t0 * (pb - pa),
                                       pa + t1 * (pb - pa)))
    if not dash_lines:
        return pv.PolyData(pts, lines=np.array([2, 0, 1]))

    new_pts = []
    cells = []
    for idx, (p0, p1) in enumerate(dash_lines):
        new_pts.append(p0)
        new_pts.append(p1)
        cells.extend([2, idx * 2, idx * 2 + 1])
    return pv.PolyData(np.array(new_pts), lines=np.array(cells, dtype=np.int64))


def region_surface(spec: AtlasSpec, smooth_sigma: float = 1.5,
                   subdivide: int = 3, smooth_iter: int = 60):
    """脑区真实形态表面 (mask -> marching cubes -> 平滑).

    整体表面 (默认, 供 voronoi_partition 表面级划分用).
    """
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


def split_mask_voxel_voronoi(spec: AtlasSpec,
                             smooth_sigma: float = 1.2,
                             subdivide: int = 3,
                             smooth_iter: int = 60) -> Dict[str, "pv.PolyData"]:
    """体素级 Voronoi 分割: 每个体素归最近亚区中心.

    每个亚区独立 mask -> 各自 marching_cubes + 平滑.
    各亚区之间天然分离 (无共享边界), 渲染时无交界线, 每亚区见顶平滑.
    """
    import nibabel as nib
    import pyvista as pv
    from skimage.measure import marching_cubes
    from scipy.ndimage import gaussian_filter
    from scipy.spatial import cKDTree

    mask = np.asarray(spec.region_mask_fn(), dtype=bool)
    aff = spec.region_mask_affine_fn()
    inv = np.linalg.inv(aff)

    # 亚区中心 -> 体素坐标
    centers_vox = []
    for s in spec.subregions:
        v = inv @ np.array([s.mni_center[0], s.mni_center[1],
                            s.mni_center[2], 1.0])
        centers_vox.append([v[0], v[1], v[2]])
    centers_vox = np.array(centers_vox)

    # 体素最近分配
    vox_coords = np.argwhere(mask)
    tree = cKDTree(centers_vox)
    _, assign = tree.query(vox_coords)
    names = [s.name for s in spec.subregions]

    out = {}
    for k, name in enumerate(names):
        sel = vox_coords[assign == k]
        if len(sel) < 10:
            continue
        sub_mask = np.zeros_like(mask)
        sub_mask[sel[:, 0], sel[:, 1], sel[:, 2]] = True
        vol = gaussian_filter(sub_mask.astype(np.float32),
                              sigma=smooth_sigma)
        pad = 6
        volp = np.pad(vol, pad, mode='constant')
        try:
            verts, faces, _, _ = marching_cubes(volp, level=0.5, step_size=1)
        except Exception:
            continue
        verts = verts - pad
        mm = (aff[:3, :3] @ verts.T).T + aff[:3, 3]
        mesh = pv.PolyData(mm, np.hstack([np.full((faces.shape[0], 1), 3),
                                          faces]).astype(np.int64).ravel())
        mesh = mesh.subdivide(subdivide, subfilter='loop').smooth(
            n_iter=smooth_iter, relaxation_factor=0.05)
        out[name] = mesh
    return out


# --------------------------------------------------------------------------
# 主渲染
# --------------------------------------------------------------------------
def visualize_subregions(
    spec: AtlasSpec,
    output: Optional[str] = None,
    view: str = 'iso',
    add_labels: bool = True,
    show_legend: bool = True,
    show_boundaries: bool = False,    # 默认无虚线 (参考图风格); 需分隔时打开
    boundary_color: str = '#909090',
    boundary_radius: float = 0.35,
    dash_ratio: float = 0.5,
    dash_segments: int = 6,
    label_offsets: Optional[Dict[str, np.ndarray]] = None,
    alpha_brain: float = 0.05,         # 淡玻璃
    alpha_region: float = 0.75,        # 亚区更实 (参考图)
    return_plotter: bool = False,
    mni152_path: Optional[str] = None,
    camera_zoom: float = 1.35,
):  # -> bool | "pv.Plotter"  (return_plotter=True 时返回 Plotter)
    """渲染玻璃脑 + 亚区果冻. 返回 None / 保存图片 / 或 plotter (交互)."""
    import pyvista as pv
    from PIL import Image

    brain = make_glass_brain(mni152_path)
    # 体素级分割: 每亚区独立 mask -> 独立平滑 surface (无交界线)
    sub = split_mask_voxel_voronoi(spec)

    pl = pv.Plotter(off_screen=(not return_plotter), window_size=[1600, 1100])
    pl.set_background('#FFFFFF')

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

    # ---------------- 玻璃脑 (淡蓝半透明, 参考 insula_yeo_iso) ----------------
    pl.add_mesh(brain, color='#B8CBE0', opacity=alpha_brain,
                smooth_shading=True, diffuse=0.5, ambient=0.55,
                specular=0.6, specular_power=128, metallic=0.0,
                roughness=0.2, show_edges=False)

    # ---------------- 岛叶亚区 (Yeo 网络色, 各自独立平滑) ----------------
    # 每个亚区用其 Yeo-7 网络色 (参考图风格: 左团紫红 VAN, 右团蓝紫 SM)
    for s in spec.subregions:
        sm = sub.get(s.name)
        if sm is None:
            continue
        rgb = YeoNetwork.RGB[s.yeo7 - 1]
        pl.add_mesh(sm, color=tuple(rgb), opacity=alpha_region,
                    smooth_shading=True, specular=0.6, specular_power=64,
                    roughness=0.25, metallic=0.0, diffuse=0.85, ambient=0.45,
                    show_edges=False, lighting=True)

    # ---------------- 分区边界线 (可选; 默认关闭) ----------------
    if show_boundaries:
        surf = region_surface(spec)
        centers = [s.mni_center for s in spec.subregions]
        names = [s.name for s in spec.subregions]
        bnd = dashed_boundary_lines(surf, centers, names,
                                    dash_ratio=dash_ratio,
                                    n_segments=dash_segments, lift=1.0)
        bnd = bnd.tube(radius=boundary_radius)
        pl.add_mesh(bnd, color=boundary_color,
                    smooth_shading=False, lighting=False, pickable=False,
                    opacity=1.0)

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

    if return_plotter or add_labels:
        # 3D 标签: 贴亚区 mesh 实际中心; 名称 = 脑区名 (short), 底板 = 所属网络色
        if add_labels:
            for s in spec.subregions:
                sm = sub.get(s.name)
                if sm is None:
                    continue
                anchor = np.array(sm.center, dtype=float)
                if label_offsets and s.name in label_offsets:
                    anchor = anchor + np.asarray(label_offsets[s.name],
                                                 dtype=float)
                rgb = YeoNetwork.RGB[s.yeo7 - 1]
                # 深色底板 -> 白字; 浅色底板 -> 黑字
                lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                text = '#FFFFFF' if lum < 0.55 else '#202020'
                shape = '#%02X%02X%02X' % tuple(int(v * 255) for v in rgb)
                lbl = f'{s.short} · {s.name}' if s.short else s.name
                pl.add_point_labels(
                    [anchor], [lbl], font_size=15,
                    show_points=False, text_color=text,
                    shape_color=shape, shape_opacity=0.9,
                    always_visible=True)

    if return_plotter:
        return pl

    pl.screenshot(output)
    pl.close()
    if show_legend:
        add_pil_legend(output, YeoNetwork.NAMES, YeoNetwork.HEX,
                       title='Yeo-7 Networks')
    return True


def export_pdf(png_path: str, pdf_path: str):
    """把渲染的 PNG 转成 PDF (多页可追加)."""
    from PIL import Image
    img = Image.open(png_path).convert('RGB')
    img.save(pdf_path, 'PDF', resolution=150.0)
    return pdf_path


def render_region(atlas: str, region: str = 'insula', output: str = None,
                  view: str = 'iso', **kwargs):
    """一键式入口: 指定图谱 + 脑区 -> 渲染 (含虚线边界/标签/图例默认开启).

    等价于 get_spec(atlas, region) 后调用 visualize_subregions.
    """
    from . import atlases
    spec = atlases.get_spec(atlas, region)
    if output is None:
        output = f'{atlas}_{region}_{view}.png'
    return visualize_subregions(spec, output=output, view=view, **kwargs)


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
        # 短名标签 (Ins_L_1 格式, 参考图样式)
        short = s.name
        anchors.append((float(sx), float(sy), s.name, short))

    placed = []
    for sx, sy, name, full in anchors:
        tw = draw.textlength(full, font=font)
        th = 24
        # 标签直接贴锚点 (居中), 无引线
        lx, ly = sx - tw / 2, sy - th / 2
        tries = 0
        while any(abs(lx - px) < tw + 10 and abs(ly - py) < th + 8
                  for px, py, *_ in placed):
            ly -= 28  # 向上避让
            tries += 1
            if tries > 60:
                break
        placed.append((lx, ly, tw, th))
        rgb = YeoNetwork.RGB[s.yeo7 - 1]
        hexc = '#%02X%02X%02X' % tuple(int(v * 255) for v in rgb)
        # 白底小标签 (贴亚区, 参考图样式)
        draw.rounded_rectangle([lx - 4, ly - 4, lx + tw + 6, ly + th + 2],
                               radius=4, fill=(255, 255, 255, 235),
                               outline=(120, 120, 120), width=1)
        draw.text((lx, ly - 1), full, fill=(30, 30, 30), font=font)

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
