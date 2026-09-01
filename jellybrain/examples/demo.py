# -*- coding: utf-8 -*-
"""jellybrain 完整示例: 指定图谱即可可视化脑区亚区.

功能覆盖:
  1) 图谱规格 (atlases.get_spec)
  2) 静态渲染 (三视角, 虚线边界 + 标签 + 图例)
  3) 交互式 HTML (trame, 可旋转 + 截图)
  4) PDF 导出
  5) 自定义标签位置 (label_offsets)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jellybrain import atlases
from jellybrain.core import (visualize_subregions, export_pdf)

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'images')
os.makedirs(IMG, exist_ok=True)

# 1. 取图谱规格 (指定图谱 + 脑区)
spec = atlases.get_spec('brainnetome', 'insula')
print('图谱:', spec.atlas_name, '| 脑区:', spec.region_name,
      '| 亚区数:', len(spec.subregions))
for s in spec.subregions[:4]:
    print('  -', s.name, '|', s.full_name, '| Yeo7 =', s.yeo7)

# 2. 静态渲染: 三视角 (虚线边界 + iso 带标签图例)
for view in ['iso', 'front', 'top']:
    out = os.path.join(IMG, f'lib_{view}.png')
    visualize_subregions(spec, output=out, view=view,
                         add_labels=(view == 'iso'), show_legend=True,
                         show_boundaries=True)
    print('PNG   ->', out)

# 3. 交互式 HTML (trame viewer, 浏览器打开可旋转/截图)
out_html = os.path.join(IMG, 'insula_interactive.html')
pl = visualize_subregions(spec, return_plotter=True,
                          add_labels=True, show_legend=False,
                          show_boundaries=True)
pl.export_html(out_html)
pl.close()
print('HTML  ->', out_html)

# 4. PDF 导出
out_pdf = os.path.join(IMG, 'lib_iso.pdf')
export_pdf(os.path.join(IMG, 'lib_iso.png'), out_pdf)
print('PDF   ->', out_pdf)

# 5. 自定义标签位置 (屏幕像素偏移)
out_custom = os.path.join(IMG, 'lib_iso_custom_labels.png')
visualize_subregions(spec, output=out_custom, view='iso',
                     add_labels=True, show_legend=True,
                     show_boundaries=True,
                     label_offsets={'Ins_L_1': (-40, 50),
                                    'Ins_R_3': (50, -40)})
print('CUSTOM->', out_custom)

# 6. 交互式窗口 (Jupyter 内)
# pl = visualize_subregions(spec, return_plotter=True)
# pl.show(jupyter_backend='trame')

print('DONE')
