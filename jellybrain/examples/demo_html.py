# -*- coding: utf-8 -*-
"""jellybrain 完整演示: 分区边界线 + 自定义标签 + HTML/PNG/PDF 导出.

  1. 静态 PNG (带边界线 + 图例 + 智能标签)
  2. 交互式 HTML (trame, 自带截图按钮可导出 PNG)
  3. PDF 导出 (从高分辨率 PNG 转换)
  4. 标签位置自定义 (label_offsets 屏幕像素偏移)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jellybrain import atlases
from jellybrain.core import visualize_subregions, export_pdf

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(ROOT, 'images')
os.makedirs(IMG, exist_ok=True)

spec = atlases.get_spec('brainnetome', 'insula')

# ---- 1. 静态 PNG (边界线 + 标签 + 图例) ----
out_png = os.path.join(IMG, 'lib_iso.png')
visualize_subregions(spec, output=out_png, view='iso',
                     add_labels=True, show_legend=True,
                     show_boundaries=True)
print('PNG   ->', out_png)

# ---- 2. 交互式 HTML (trame viewer, 自带 Save 截图按钮导出 PNG) ----
out_html = os.path.join(IMG, 'insula_interactive.html')
pl = visualize_subregions(spec, return_plotter=True,
                          add_labels=True, show_legend=False,
                          show_boundaries=True)
pl.export_html(out_html)
pl.close()
print('HTML  ->', out_html)

# ---- 3. PDF 导出 ----
out_pdf = os.path.join(IMG, 'lib_iso.pdf')
export_pdf(out_png, out_pdf)
print('PDF   ->', out_pdf)

# ---- 4. 标签位置自定义示例 ----
offsets = {
    # 手动把部分标签移到更佳位置 (屏幕像素 dx, dy)
    'Ins_L_1': (-30, 40),
    'Ins_L_2': (-60, 20),
    'Ins_R_3': (40, -30),
}
out_custom = os.path.join(IMG, 'lib_iso_custom_labels.png')
visualize_subregions(spec, output=out_custom, view='iso',
                     add_labels=True, show_legend=True,
                     show_boundaries=True, label_offsets=offsets)
print('CUSTOM->', out_custom)
print('DONE')
