# -*- coding: utf-8 -*-
"""jellybrain 冒烟测试: 确认库可导入、规格正确、渲染管线基本工作."""
import os
import tempfile


def test_spec():
    from jellybrain import atlases
    spec = atlases.get_spec('brainnetome', 'insula')
    assert spec.atlas_name == 'brainnetome'
    assert spec.region_name == 'insula'
    assert len(spec.subregions) == 12
    # 左右对称: 6 左 + 6 右
    names = [s.name for s in spec.subregions]
    assert all(s.yeo7 in range(1, 8) for s in spec.subregions)
    print('OK spec:', len(spec.subregions), 'subregions')


def test_render_pipeline(tmp_path=None):
    """仅验证管线能跑通 (玻璃脑 + 形态 + 划分 + 截图)."""
    from jellybrain import atlases
    from jellybrain.core import (region_surface, voronoi_partition,
                                 make_glass_brain)
    spec = atlases.get_spec('brainnetome', 'insula')
    brain = make_glass_brain()
    assert brain.n_points > 1000
    surf = region_surface(spec)
    assert surf.n_points > 500
    sub = voronoi_partition(
        surf, [s.mni_center for s in spec.subregions],
        [s.name for s in spec.subregions])
    assert len(sub) == 12
    print('OK pipeline: brain', brain.n_points, 'surf', surf.n_points,
          'sub', len(sub))


if __name__ == '__main__':
    test_spec()
    test_render_pipeline()
    print('ALL TESTS PASSED')
