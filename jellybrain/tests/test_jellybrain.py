# -*- coding: utf-8 -*-
"""jellybrain 测试套件: 覆盖 规格/渲染管线/虚线/分区/导出."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ---------------------------------------------------------------- 规格
def test_spec():
    from jellybrain import atlases
    spec = atlases.get_spec('brainnetome', 'insula')
    assert spec.atlas_name == 'brainnetome'
    assert spec.region_name == 'insula'
    assert len(spec.subregions) == 12
    assert all(isinstance(s.yeo7, int) and 1 <= s.yeo7 <= 7
               for s in spec.subregions)
    # 唯一名 (左右各 6)
    names = [s.name for s in spec.subregions]
    assert len(set(names)) == 12
    # 已知官方映射: Ins_L_1 = Somatomotor(2), Ins_L_2 = Frontoparietal(6)
    m = {s.name: s.yeo7 for s in spec.subregions}
    assert m['Ins_L_1'] == 2
    assert m['Ins_L_2'] == 6
    assert m['Ins_L_3'] == 4
    print('OK test_spec')


# ---------------------------------------------------------------- 玻璃脑
def test_glass_brain():
    from jellybrain.core import make_glass_brain
    b = make_glass_brain()
    assert b.n_points > 100000
    assert b.n_cells > 200000
    print('OK test_glass_brain', b.n_points)


# ---------------------------------------------------------------- 形态+分区
def test_region_and_voronoi():
    from jellybrain import atlases
    from jellybrain.core import (region_surface, voronoi_partition)
    spec = atlases.get_spec('brainnetome', 'insula')
    surf = region_surface(spec)
    assert surf.n_points > 50000
    sub = voronoi_partition(
        surf, [s.mni_center for s in spec.subregions],
        [s.name for s in spec.subregions])
    assert len(sub) == 12
    for k, m in sub.items():
        assert m.n_cells > 0
    print('OK test_region_and_voronoi', surf.n_points, len(sub))


# ---------------------------------------------------------------- 虚线
def test_dashed_boundary():
    from jellybrain import atlases
    from jellybrain.core import (region_surface, dashed_boundary_lines)
    spec = atlases.get_spec('brainnetome', 'insula')
    surf = region_surface(spec)
    centers = [s.mni_center for s in spec.subregions]
    names = [s.name for s in spec.subregions]
    bnd = dashed_boundary_lines(surf, centers, names,
                                dash_ratio=0.5, n_segments=6)
    assert bnd.n_cells > 1000
    # 虚线段是短线 (每 cell 2 点)
    assert bnd.n_points == bnd.n_cells * 2
    print('OK test_dashed_boundary', bnd.n_cells)


# ---------------------------------------------------------------- 导出
def test_exports(tmpdir='.'):
    from jellybrain import atlases
    from jellybrain.core import (visualize_subregions, export_pdf)
    spec = atlases.get_spec('brainnetome', 'insula')
    png = os.path.join(tmpdir, '_t.png')
    ok = visualize_subregions(spec, output=png, view='front',
                              add_labels=False, show_legend=False)
    assert ok and os.path.exists(png) and os.path.getsize(png) > 50000
    # PDF
    pdf = os.path.join(tmpdir, '_t.pdf')
    export_pdf(png, pdf)
    assert os.path.exists(pdf) and os.path.getsize(pdf) > 1000
    # 自定义标签偏移
    png2 = os.path.join(tmpdir, '_t2.png')
    visualize_subregions(spec, output=png2, view='iso',
                         label_offsets={'Ins_L_1': (50, 50)})
    assert os.path.exists(png2)
    os.remove(png); os.remove(png2)
    try:
        os.remove(pdf)
    except Exception:
        pass
    print('OK test_exports')


# ---------------------------------------------------------------- HTML
def test_html_export():
    from jellybrain import atlases
    from jellybrain.core import visualize_subregions
    spec = atlases.get_spec('brainnetome', 'insula')
    html = os.path.join(os.path.dirname(__file__), '_t.html')
    pl = visualize_subregions(spec, return_plotter=True, add_labels=False)
    pl.export_html(html)
    pl.close()
    assert os.path.exists(html) and os.path.getsize(html) > 1000000
    os.remove(html)
    print('OK test_html_export')


if __name__ == '__main__':
    test_spec()
    test_glass_brain()
    test_region_and_voronoi()
    test_dashed_boundary()
    test_exports()
    test_html_export()
    print('ALL TESTS PASSED')
