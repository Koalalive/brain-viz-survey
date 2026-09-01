# -*- coding: utf-8 -*-
"""一键生成全部交付物: 交互HTML(可导出PNG/PDF/TIF) + 三角度 PNG/PDF/TIF.

  1. interactive HTML viewer (浏览器旋转, 右上角工具栏导出当前视角 PNG/PDF/TIF)
  2. 批量导出 iso/front/top 三角度 PNG/PDF/TIF
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

os.system(f'"{sys.executable}" "{os.path.join(os.path.dirname(__file__), "export_viewer.py")}" --html')
os.system(f'"{sys.executable}" "{os.path.join(os.path.dirname(__file__), "..", "scripts", "inject_toolbar.py")}" '
          f'"{os.path.join(os.path.dirname(__file__), "..", "..", "images", "insula_viewer.html")}" '
          f'"{os.path.join(os.path.dirname(__file__), "..", "..", "images", "insula_viewer_exports.html")}"')
os.system(f'"{sys.executable}" "{os.path.join(os.path.dirname(__file__), "export_viewer.py")}" --angles iso,front,top')
print('DONE. 产物见 images/: insula_viewer_exports.html (交互, 可导出), insula_{iso,front,top}.{png,pdf,tif}')
