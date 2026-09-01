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
    render_region,
    make_glass_brain,
    voronoi_partition,
    voronoi_boundary_lines,
    dashed_boundary_lines,
    split_mask_voxel_voronoi,
    export_pdf,
)
from . import atlases

__version__ = "0.2.0"
__all__ = [
    "AtlasSpec", "Subregion", "YeoNetwork",
    "visualize_subregions", "render_region", "make_glass_brain",
    "voronoi_partition", "voronoi_boundary_lines", "dashed_boundary_lines",
    "split_mask_voxel_voronoi", "export_pdf", "atlases",
]
