# -*- coding: utf-8 -*-
"""标定: 各亚区 mesh 中心在固定 iso 视角下的屏幕坐标 (vtk world_to_display)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pyvista as pv

from jellybrain import atlases
from jellybrain.core import (make_glass_brain,
                             split_mask_voxel_voronoi)

W, H = 1280, 900

spec = atlases.get_spec('brainnetome', 'insula')
brain = make_glass_brain()
sub = split_mask_voxel_voronoi(spec)

pl = pv.Plotter(off_screen=True, window_size=[W, H])
pl.set_background('#FFFFFF')
pl.add_mesh(brain, color='#B8CBE0', opacity=0.05)
for s in spec.subregions:
    sm = sub.get(s.name)
    if sm is None:
        continue
    pl.add_mesh(sm, color=(0.5, 0.5, 0.5), opacity=0.75)

pl.camera_position = [(280.0, -280.0, 240.0), (0, 0, 5), (0, 0, 1)]
pl.reset_camera()
pl.camera.zoom(1.35)
ren = pl.renderer
ren.Render()

out = {}
for s in spec.subregions:
    sm = sub.get(s.name)
    if sm is None:
        continue
    c = np.array(sm.center, dtype=float)
    d = np.array(ren.world_to_display(c))
    # vtk 用左下原点; 网页用左上 (翻转 y)
    out[s.name] = {
        'world': [float(x) for x in c],
        'display': [float(d[0]), float(H - d[1])],
    }
    print(f'{s.name}: world={c.round(1)} display=({d[0]:.0f},{H-d[1]:.0f})')

pl.close()
with open(os.path.join(os.path.dirname(__file__), '..', '..', 'images',
                       'label_positions.json'), 'w') as f:
    json.dump(out, f, indent=2)
print('saved label_positions.json')
