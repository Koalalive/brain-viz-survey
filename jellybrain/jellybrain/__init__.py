# -*- coding: utf-8 -*-
"""jellybrain: 玻璃脑果冻风格脑区亚区可视化库.

指定脑图谱 + 脑区即可渲染对应亚区的 3D 玻璃脑可视化.
例:  atlases.brainnetome_insula() -> render()
"""
from .core import (
    AtlasSpec,
    Subregion,
    YeoNetwork,
    visualize_subregions,
    make_glass_brain,
    voronoi_partition,
)
from . import atlases

__version__ = "0.1.0"
__all__ = [
    "AtlasSpec", "Subregion", "YeoNetwork",
    "visualize_subregions", "make_glass_brain", "voronoi_partition",
    "atlases",
]
