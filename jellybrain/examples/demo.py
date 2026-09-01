# -*- coding: utf-8 -*-
"""jellybrain 示例: 指定图谱即可可视化脑区亚区.

  1) 内置图谱: atlases.get_spec('brainnetome', 'insula')
  2) 渲染:  visualize_subregions(spec, output=..., view=...)
"""
import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jellybrain import atlases
from jellybrain.core import visualize_subregions

# 1. 取图谱规格 (指定图谱 + 脑区)
spec = atlases.get_spec('brainnetome', 'insula')
print('图谱:', spec.atlas_name, '| 脑区:', spec.region_name,
      '| 亚区数:', len(spec.subregions))
for s in spec.subregions[:4]:
    print('  -', s.name, '|', s.full_name, '| Yeo7 =', s.yeo7)

# 2. 静态渲染: 三视角
root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'images'))
os.makedirs(root, exist_ok=True)
for view in ['iso', 'front', 'top']:
    out = os.path.join(root, f'lib_{view}.png')
    visualize_subregions(spec, output=out, view=view,
                         add_labels=(view == 'iso'), show_legend=True)
    print('saved:', out)

# 3. 交互式 (Jupyter 里打开 / 导出 HTML)
# pl = visualize_subregions(spec, return_plotter=True)
# pl.show(jupyter_backend='trame')
# pl.export_html(os.path.join(root, 'lib_interactive.html'))
