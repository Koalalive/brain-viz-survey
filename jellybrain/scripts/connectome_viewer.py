# -*- coding: utf-8 -*-
"""jellybrain 脑网络球棒图 (BrainNet Viewer 风格).

玻璃脑 + BNA 岛叶 12 亚区球节点 (Yeo-7 配色) + 网络边, 出版级 PNG/PDF/TIF.
零新增依赖 (pyvista + networkx + nilearn + PIL, 均为 jellybrain 既有栈).

用法:
  python scripts/connectome_viewer.py                       # 默认三视角
  python scripts/connectome_viewer.py --angles iso,front,top
  python scripts/connectome_viewer.py --html                # 额外生成交互 HTML
  python scripts/connectome_viewer.py --edges 阈值边数 [--seed 42]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'images')
os.makedirs(IMG, exist_ok=True)

VIEW_ANGLES = {
    'iso': [(280.0, -280.0, 240.0), (0, 0, 5), (0, 0, 1)],
    'front': [(0, -400.0, 10.0), (0, 0, 0), (0, 0, 1)],
    'top': [(0, 0, 500.0), (0, 0, 0), (0, 1, 0)],
    'side': [(400.0, 0, 10.0), (0, 0, 0), (0, 0, 1)],
    'back': [(0, 400.0, 10.0), (0, 0, 0), (0, 0, 1)],
}


def build_edges(net_nodes, n_edges=12, seed=42, rng=None):
    """按先生成网络内边-后跨网络边的策略生成边列表 (确定性).

    返回 [(i, j), ...] 节点索引对 (i<j), 每条边附可选权重.
    """
    import networkx as nx

    rng = rng or np.random.default_rng(seed)
    G = nx.Graph()
    G.add_nodes_from(range(len(net_nodes)))
    # 优先同网络连接 (解剖/网络合理), 再跨网络补足
    same_net = {i: net_nodes[i]['yeo'] for i in range(len(net_nodes))}
    same = [(i, j) for i in range(len(net_nodes))
            for j in range(i + 1, len(net_nodes))
            if same_net[i] == same_net[j]]
    cross = [(i, j) for i in range(len(net_nodes))
             for j in range(i + 1, len(net_nodes))
             if same_net[i] != same_net[j]]
    rng.shuffle(same)
    rng.shuffle(cross)
    edges = []
    target_input = None
    edges = []
    # 交替取同网/跨网, 凑足 n_edges
    k = 0
    while len(edges) < n_edges and (k < len(same) or k < len(cross)):
        if k < len(same):
            edges.append(same[k])
        if len(edges) < n_edges and k < len(cross):
            edges.append(cross[k])
        k += 1
    return edges[:n_edges]


def render_connectome(out_prefix='insula_connectome', angles=('iso',),
                      n_edges=12, seed=42, html=False, suffix=None):
    """渲染脑网络球棒图 (玻璃脑 + 节点球 + 边)."""
    import pyvista as pv
    from PIL import Image

    from jellybrain import atlases
    from jellybrain.core import make_glass_brain, YeoNetwork, add_pil_legend

    spec = atlases.get_spec('brainnetome', 'insula')
    centers = {s.name: np.asarray(s.mni_center, dtype=float)
               for s in spec.subregions}
    names = [s.name for s in spec.subregions]
    net_nodes = [{'name': s.name, 'yeo': s.yeo7, 'center': centers[s.name]}
                 for s in spec.subregions]
    edges = build_edges(net_nodes, n_edges=n_edges, seed=seed)

    # 每个视角单独渲染 (避免视角串扰)
    paths = []
    for ang in angles:
        if ang not in VIEW_ANGLES:
            print(f'  [skip] unknown angle {ang}')
            continue
        pl = pv.Plotter(off_screen=True, window_size=[1600, 1100])
        pl.set_background('#FFFFFF')
        # 玻璃脑
        brain = make_glass_brain()
        pl.add_mesh(brain, color='#B8CBE0', opacity=0.05, smooth_shading=True,
                    diffuse=0.5, ambient=0.55, specular=0.6,
                    specular_power=128)
        # 边 (紫灰细管)
        for i, j in edges:
            p0, p1 = net_nodes[i]['center'], net_nodes[j]['center']
            n = 24
            t = np.linspace(0, 1, n)[:, None]
            line = (1 - t) * p0 + t * p1
            tube = pv.lines_from_points(line)
            pl.add_mesh(tube, color='#8888AA', opacity=0.55, line_width=2.5)
        # 节点球 (Yeo-7 配色, 半径按体素规模近似)
        for k, nd in enumerate(net_nodes):
            rgb = YeoNetwork.RGB[nd['yeo'] - 1]
            sphere = pv.Sphere(radius=5.5, center=nd['center'],
                               theta_resolution=40, phi_resolution=40)
            pl.add_mesh(sphere, color=tuple(rgb), opacity=0.95,
                        smooth_shading=True, specular=0.7,
                        specular_power=64, roughness=0.2,
                        diffuse=0.85, ambient=0.45)
        pos, foc, up = VIEW_ANGLES[ang]
        pl.camera_position = [list(pos), list(foc), list(up)]
        pl.reset_camera()
        png = os.path.join(IMG, f'{out_prefix}_{ang}.png')
        pl.screenshot(png)
        pl.close()
        # 图例 (Yeo-7)
        add_pil_legend(png, YeoNetwork.NAMES, YeoNetwork.HEX,
                       title='Yeo-7 Networks')
        # PDF + TIF
        pdf = os.path.join(IMG, f'{out_prefix}_{ang}.pdf')
        Image.open(png).convert('RGB').save(pdf, 'PDF', resolution=150.0)
        tif = os.path.join(IMG, f'{out_prefix}_{ang}.tif')
        Image.open(png).convert('RGB').save(tif, 'TIFF', dpi=(300, 300))
        paths.append((ang, png, pdf, tif))
        print(f'  {ang}: png={os.path.basename(png)} pdf='
              f'{os.path.basename(pdf)} tif={os.path.basename(tif)}')
    if html:
        # 交互 HTML: 复用 visualize_subregions 出网状图
        import pyvista as pv
        pl2 = pv.Plotter(window_size=[1280, 900])
        pl2.set_background('#FFFFFF')
        brain = make_glass_brain()
        pl2.add_mesh(brain, color='#B8CBE0', opacity=0.05, smooth_shading=True,
                     diffuse=0.5, ambient=0.55, specular=0.6,
                     specular_power=128)
        for i, j in edges:
            p0, p1 = net_nodes[i]['center'], net_nodes[j]['center']
            line = pv.lines_from_points(
                np.linspace(0, 1, 24)[:, None] * (p1 - p0) + p0)
            pl2.add_mesh(line, color='#8888AA', opacity=0.55, line_width=2.5)
        for nd in net_nodes:
            rgb = YeoNetwork.RGB[nd['yeo'] - 1]
            pl2.add_mesh(pv.Sphere(radius=5.5, center=nd['center']),
                         color=tuple(rgb), opacity=0.95, smooth_shading=True)
        pl2.camera_position = [list(VIEW_ANGLES['iso'][0]),
                               list(VIEW_ANGLES['iso'][1]),
                               list(VIEW_ANGLES['iso'][2])]
        pl2.reset_camera()
        h = os.path.join(IMG, f'{out_prefix}.html')
        pl2.export_html(h)
        pl2.close()
        print(f'  html: {os.path.basename(h)}')
    return paths


def main():
    p = argparse.ArgumentParser(description='脑网络球棒图 (BrainNet Viewer 风格)')
    p.add_argument('--angles', default='iso,front,top',
                   help='逗号分隔视角 (iso,front,top,side,back), 默认 iso,front,top')
    p.add_argument('--edges', type=int, default=12, help='生成的边数, 默认 12')
    p.add_argument('--seed', type=int, default=42, help='随机种子 (确定性), 默认 42')
    p.add_argument('--html', action='store_true', help='额外生成交互 HTML')
    p.add_argument('--prefix', default='insula_connectome',
                   help='输出文件名前缀, 默认 insula_connectome')
    a = p.parse_args()
    angles = tuple(x.strip() for x in a.angles.split(',') if x.strip())
    render_connectome(out_prefix=a.prefix, angles=angles, n_edges=a.edges,
                      seed=a.seed, html=a.html)


if __name__ == '__main__':
    main()
