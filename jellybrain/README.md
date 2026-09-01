# jellybrain

**玻璃脑果冻风格脑区亚区可视化库** —— 指定脑图谱,即可可视化该图谱下脑区的各个亚区(半透明玻璃脑 + 亚区真实形态 + Yeo-7 网络配色 + 图例/标签/交互)。

## 安装

```bash
pip install -e .
# 交互式 (Jupyter trame / HTML 导出) 附加依赖:
pip install -e ".[jupyter]"
```

## 快速开始

```python
from jellybrain import atlases
from jellybrain.core import visualize_subregions

# 1) 指定图谱 + 脑区 -> 获取图谱规格
spec = atlases.get_spec('brainnetome', 'insula')   # Brainnetome Atlas 岛叶

# 2) 渲染静态图 (三视角; show_boundaries 显示分区边界线)
visualize_subregions(spec, output='insula_iso.png', view='iso',
                     show_boundaries=True)

# 3) 标签位置自定义 (屏幕像素偏移 {name: (dx, dy)})
offsets = {'Ins_L_1': (-30, 40), 'Ins_R_3': (40, -30)}
visualize_subregions(spec, output='custom.png', label_offsets=offsets)

# 4) 交互式 3D (Jupyter 内, trame 自带截图按钮可导出 PNG)
pl = visualize_subregions(spec, return_plotter=True, show_boundaries=True)
pl.show(jupyter_backend='trame')

# 5) 导出自包含交互 HTML (浏览器打开, 可旋转 + 截图导出 PNG)
pl = visualize_subregions(spec, return_plotter=True)
pl.export_html('insula_interactive.html')

# 6) 导出 PDF (从渲染 PNG 转换)
from jellybrain.core import export_pdf
visualize_subregions(spec, output='insula.png')
export_pdf('insula.png', 'insula.pdf')
```

## 命令行

```bash
jellybrain --atlas brainnetome --region insula -o out.png       # 默认 iso
jellybrain --atlas brainnetome --view top -o top.png
jellybrain --atlas brainnetome --html ins.html                  # 交互 HTML
```

## 核心概念

```python
@dataclass
class Subregion:
    name: str          # 短名, 如 "dIa"
    full_name: str     # 全名, 如 "dorsal agranular"
    mni_center: np.ndarray  # MNI 中心 (mm), Voronoi 划分用
    yeo7: int          # Yeo-7 网络编号 (1-7), 配色用

@dataclass
class AtlasSpec:
    atlas_name: str        # "brainnetome"
    region_name: str       # "insula"
    subregions: List[Subregion]
    region_mask_fn: Callable[[], np.ndarray]        # 脑区 ROI mask
    region_mask_affine_fn: Callable[[], np.ndarray] # 对应 affine
```

**扩展新图谱**: 实现 `AtlasSpec` 即集成 —— 提供亚区列表(name/full_name/center/yeo7)+ 脑区 mask 函数 + affine。渲染引擎 (玻璃脑 / Voronoi 划分 / 果冻材质 / 图例 / 标签) 完全通用。

## 内置图谱

### Brainnetome Atlas — Insula (`get_spec('brainnetome', 'insula')`)

- **亚区**: BNA 岛叶 12 亚区 (INS-1~6 左右) —— G / vIa / dIa / vId·vIg / dIg / dId
- **Yeo-7 归属**: 官方 `subregion_func_network_Yeo_updated.csv` (label 163-174)
- **形态来源**: AAL 岛叶真实皮层 mask → marching cubes → 平滑
- **亚区中心**: BNA `data_centers.json`

| 编号 | 短名 | 全名 | Yeo-7 |
|---|---|---|---|
| INS-1 | G | hypergranular | Somatomotor |
| INS-2 | vIa | ventral agranular | Frontoparietal |
| INS-3 | dIa | dorsal agranular | Ventral Attention |
| INS-4 | vId/vIg | ventral dysgranular/granular | Ventral Attention |
| INS-5 | dIg | dorsal granular | Somatomotor |
| INS-6 | dId | dorsal dysgranular | Ventral Attention |

## 渲染管线

1. **玻璃脑**: MNI152 模板 (nilearn 自动获取) → marching cubes → Loop 细分 + 平滑
2. **脑区形态**: 图谱 ROI mask → 高斯平滑 → marching cubes → 细分 3 次 + 平滑 (真实沟回形态)
3. **亚区划分**: 亚区 MNI 中心 → **Voronoi 划分** (每块保留真实形态)
4. **分区边界线**: 相邻亚区共享边提取 → tube 化 → 深灰高对比边界 (清晰展示亚区分界)
5. **材质**: 果冻质感 (半透明 + 高光泽 + 低粗糙度) + **Yeo-7 官方配色**
6. **标签**: PIL 智能排布 (不重叠 + 引线 + 可自定义 `label_offsets` 屏幕偏移)
7. **图例**: Yeo-7 七色图例 (PIL 叠加)

## 导出格式

| 格式 | 方式 | 说明 |
|---|---|---|
| PNG | `visualize_subregions(..., output='x.png')` | 静态成品图 (边界线+标签+图例) |
| 交互 HTML | `pl.export_html('x.html')` | trame viewer, 浏览器内旋转缩放, 自带截图按钮导出 PNG |
| PDF | `export_pdf('x.png', 'x.pdf')` | 从渲染 PNG 转换 (150 DPI) |

## 依赖

numpy, pyvista, nibabel, nilearn, scipy, scikit-image, pillow

## 许可证

MIT
