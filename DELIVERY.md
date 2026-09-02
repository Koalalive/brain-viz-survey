# brain-viz-survey 交付说明

**Brainnetome Atlas 岛叶 12 亚区可视化** — jellybrain (pyvista) 渲染管线

## 一、交付物概览

| 产物 | 位置 | 说明 |
|---|---|---|
| 交互式 HTML viewer | `images/insula_viewer_exports.html` | 浏览器打开即用: 鼠标拖拽旋转、导出 PNG/PDF/TIF、Yeo-7 图例 |
| 静态三视角图 | `images/insula_iso/front/top.png|pdf|tif` | `export_viewer.py --angles` 批量导出 |
| 脑网络球棒图 | `images/insula_connectome_*` | 玻璃脑 + 节点球 + 边 (BrainNet Viewer 风格) |
| 源 HTML | `images/insula_viewer.html` | 注入前原版 (含 3D 场景, 无工具栏) |

## 二、核心特性

- **玻璃脑**: MNI152 marching_cubes + 平滑, 半透明淡蓝罩
- **12 亚区核团**: 体素级 Voronoi 分割 (每体素归最近亚区中心) → 独立 marching_cubes + 平滑 → 各自果冻质感核团, 无交界线
- **Yeo-7 官方配色**: 亚区按 Brainnetome 官方 subregion_func_network_Yeo 网络归属上色
- **左右对称**: 右侧中心 = 左侧精确镜像 (x 取反), `mni_center` 镜像距离 0.0000mm, 正视 Mask IoU 0.915
- **交互**: 原生鼠标拖拽旋转 (vtk.js, 绑定主渲染器含 13 actors), 标签跟随 (3D 文字)
- **导出**: PNG / PDF (字节级内嵌真实 JPEG) / TIF (最小未压缩 TIFF, 300dpi)

## 三、网络归属 (BNA 岛叶 12 亚区)

| 亚区 | 命名 | Yeo-7 网络 | 颜色 |
|---|---|---|---|
| Ins_L_1 / Ins_R_1 | G (hypergranular) | Somatomotor | `#4682B4` |
| Ins_L_2 / Ins_R_2 | vIa (ventral agranular) | Frontoparietal | `#E69422` |
| Ins_L_3 / Ins_R_3 | dIa (dorsal agranular) | Ventral Attention | `#C43AFA` |
| Ins_L_4 / Ins_R_4 | vId/vIg (ventral dysgranular/granular) | Ventral Attention | `#C43AFA` |
| Ins_L_5 / Ins_R_5 | dIg (dorsal granular) | Somatomotor | `#4682B4` |
| Ins_L_6 / Ins_R_6 | dId (dorsal dysgranular) | Ventral Attention | `#C43AFA` |

## 四、使用说明

### 重新生成交互 HTML
```bash
cd jellybrain
python examples/export_viewer.py --html                # 生成 images/insula_viewer.html
python scripts/inject_toolbar.py `
    ../images/insula_viewer.html ../images/insula_viewer_exports.html
```

### 批量三视角导出
```bash
python examples/export_viewer.py --angles iso,front,top
```

### 脑网络球棒图
```bash
python scripts/connectome_viewer.py --angles iso,front --edges 12 --seed 42
python scripts/connectome_viewer.py --html              # 额外生成交互 HTML
```

### 验收测试
```bash
python scripts/test_exports.py   # 无标签验证 (图例/拖拽旋转/导出非空)
```

## 五、修复记录 (重要)

| 提交 | 修复 |
|---|---|
| `4c21728` | 鼠标拖拽旋转: `setCurrentRenderer` 绑定 (vtk.js style 需要) |
| `07ca77f` | 相机 `onModified → render` 强制重绘 + PDF 字节级写器 (Blob 字符串 UTF-8 破坏二进制) |
| `96095e5` | 删悬浮文字标签、保留 Yeo-7 图例、交互器绑定主渲染器 (原绑定空渲染器 0 actors) + `onInteraction→render` |
| `1f7b674` | 右半侧中心镜像重建 (data_centers.json R 侧编号置换) + 平滑参数 `sigma=0.8, iter=40, relax=0.01` (间隙 1.44→0.33mm, 体积+37%) |
| `1ee904f` | `bna_insula_spec` 右侧 = 左侧精确镜像 (x 取反), mni_center 镜像距离 0.0000mm |

## 六、已知边界

- 标签为 3D 文字 (vtkTextActor3D), 无悬浮 DOM 标签 (按需删除)
- 球棒图边为网络拓扑示意 (同网络优先 + 跨网络补足, 确定性 seed), 非真实连接矩阵
- PDF 内嵌 JPEG (非矢量), 适合网络图/示意; 矢量可用 `--angles` 版 TIF/PDF 中的 png 源
- `insula_viewer_exports.html` 约 68MB (含 3D 场景数据), 打开需数秒

## 七、目录结构

```
brain-viz-survey/
├── data/                   # BNA data_centers.json + Yeo CSV + MNI152 模板
├── images/                 # 全部输出产物
└── jellybrain/
    ├── jellybrain/
    │   ├── atlases.py      # BNA 岛叶 12 亚区规格 (镜像对称中心 + Yeo)
    │   └── core.py         # 玻璃脑/Voronoi 分割/渲染/导出
    ├── examples/
    │   └── export_viewer.py # HTML + 批量角度导出
    └── scripts/
        ├── inject_toolbar.py   # HTML 注入 (工具栏/图例/旋转/导出)
        ├── connectome_viewer.py # 脑网络球棒图
        └── test_exports.py     # 验收测试
```
