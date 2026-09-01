# -*- coding: utf-8 -*-
"""jellybrain 导出工具: 交互 HTML + 多角度批量导出 (PNG/PDF/TIF).

用法:
  python export_viewer.py --html            # 生成交互 HTML (浏览器旋转查看)
  python export_viewer.py --angles iso,front,top   # 三角度批量导出 PNG/PDF/TIF
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import numpy as np
import pyvista as pv

from jellybrain import atlases
from jellybrain.core import visualize_subregions

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


def export_html(out: str = None):
    """生成交互 HTML (trame viewer, 可旋转 + 自带截图按钮)."""
    import sys as _s
    _s.path.insert(0, os.path.join(os.path.dirname(__file__)))
    spec = atlases.get_spec('brainnetome', 'insula')
    pl = visualize_subregions(spec, return_plotter=True, add_labels=True,
                              show_legend=False)
    out = out or os.path.join(IMG, 'insula_viewer.html')
    pl.export_html(out)
    pl.close()
    print('HTML ->', out)
    return out


def export_angles(angles=('iso', 'front', 'top'), prefix='insula'):
    """按角度批量导出 PNG/PDF/TIF (off_screen 渲染)."""
    from PIL import Image
    from jellybrain import atlases as _a

    spec = atlases.get_spec('brainnetome', 'insula')
    for ang in angles:
        # 手动构建 off_screen plotter
        import pyvista as pv
        from jellybrain.core import (make_glass_brain,
                                     split_mask_voxel_voronoi,
                                     YeoNetwork, add_pil_legend)
        brain = make_glass_brain()
        sub = split_mask_voxel_voronoi(spec)
        pl = pv.Plotter(off_screen=True, window_size=[1600, 1100])
        pl.set_background('#FFFFFF')
        pl.add_mesh(brain, color='#B8CBE0', opacity=0.05,
                    smooth_shading=True, diffuse=0.5, ambient=0.55,
                    specular=0.6, specular_power=128)
        for s in spec.subregions:
            sm = sub.get(s.name)
            if sm is None:
                continue
            rgb = YeoNetwork.RGB[s.yeo7 - 1]
            pl.add_mesh(sm, color=tuple(rgb), opacity=0.75,
                        smooth_shading=True, specular=0.6,
                        specular_power=64, roughness=0.25,
                        diffuse=0.85, ambient=0.45)
        # 标签
        for s in spec.subregions:
            sm = sub.get(s.name)
            if sm is None:
                continue
            pl.add_point_labels([np.array(sm.center, dtype=float)],
                                [s.name], font_size=16, show_points=False,
                                text_color='#202020', shape_color='#FFFFFF',
                                shape_opacity=0.95, always_visible=True)
        pos, foc, up = VIEW_ANGLES[ang]
        pl.camera_position = [list(pos), list(foc), list(up)]
        pl.reset_camera()
        png = os.path.join(IMG, f'{prefix}_{ang}.png')
        pl.screenshot(png)
        pl.close()
        # 叠加图例
        add_pil_legend(png,
                       ['Visual', 'Somatomotor', 'Dorsal Attention',
                        'Ventral Attention', 'Limbic',
                        'Frontoparietal', 'Default Mode'],
                       ['#781286', '#4682B4', '#00760E', '#C43AFA',
                        '#DCF8A4', '#E69422', '#CD3E4E'],
                       title='Yeo-7 Networks')
        # PDF
        pdf = os.path.join(IMG, f'{prefix}_{ang}.pdf')
        Image.open(png).convert('RGB').save(pdf, 'PDF', resolution=150.0)
        # TIF
        tif = os.path.join(IMG, f'{prefix}_{ang}.tif')
        Image.open(png).convert('RGB').save(tif, 'TIFF', dpi=(300, 300))
        print(f'  {ang}: {png} / {pdf} / {tif}')


if __name__ == '__main__':
    if '--html' in sys.argv:
        export_html()
    if '--angles' in sys.argv:
        i = sys.argv.index('--angles')
        angles = sys.argv[i + 1].split(',') if len(sys.argv) > i + 1 \
            else ['iso', 'front', 'top']
        export_angles(angles)
    if not any(a in sys.argv for a in ('--html', '--angles')):
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('--html', action='store_true')
        p.add_argument('--angles', default=None)
        a = p.parse_args()
        if a.html:
            export_html()
        if a.angles:
            export_angles(a.angles.split(','))
