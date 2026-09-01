# 脑影像可视化软件画风与特定脑区(岛叶 / 边缘系统 / 深部核团)可视化工具包调研

> 调研日期:2026-09-01
> 范围:人脑 MRI 影像可视化(皮层表面 / 体积 / 网络),重点梳理岛叶、边缘系统、深部核团的现成工具包、图谱与库。
> 用途:为脑影像可视化(尤其在岛叶、边缘系统、深部核团方向)选型提供参考。

---

## 目录

1. [脑影像可视化软件生态与"画风"](#一脑影像可视化软件生态与画风)
2. [岛叶可视化工具与图谱](#二岛叶可视化工具与图谱)
3. [边缘系统(海马/杏仁核/扣带回)可视化工具与图谱](#三边缘系统可视化工具与图谱)
4. [深部核团可视化工具与图谱](#四深部核团可视化工具与图谱)
5. [综合选型建议](#五综合选型建议)
6. [渲染引擎与优缺点详解](#六渲染引擎与优缺点详解)
7. [参考链接与文献](#七参考链接与文献)

---

## 一、脑影像可视化软件生态与"画风"

### 1.1 三大谱系

当前脑影像可视化软件大体分为三类,画风差别明显:

| 谱系 | 代表工具 | 画风特征 | 典型用途 |
|---|---|---|---|
| **GUI 桌面端** | Surf Ice, Freeview, FSLeyes, ITK-SNAP, MRIcroGL, Connectome Workbench (wb_view), 3D Slicer | 交互式、手调参数;现代版本(shader 渲染)可出"杂志级"高品质图 | 快速查看、质控、精确调图 |
| **代码驱动(科研主流)** | nilearn, brainrender, Brainspace/surfplot, ENIGMA Toolbox, PyCortex, MNE, visbrain, ggseg(R), fsbrain(R) | 可复现、可批处理、面向"出版物级"出图;与 matplotlib/plotly/vedo/pyvista 图形引擎集成 | 发表用图、批量流水线、统计结果映射 |
| **Web / 在线** | Neuroglancer, NiiVue, BrainBrowser, brainlife.io, siibra-explorer (EBRAINS) | 浏览器内实时渲染、支持大体积数据(预计算/Zarr)、易分享 | 数据共享、在线查看、大型图谱 (Julich) 浏览 |

### 1.2 "画风"的关键维度

1. **渲染引擎与 shader 效果**:现代高端画风由可编程 shader 驱动。
   - **Surf Ice**(2025 年 Nature Methods 方法论文)是当前画风标杆:支持环境光遮蔽 (ambient occlusion)、曲率阴影、自定义 shader,用"皱褶谷暗、脑回脊亮"来凸显折叠结构,官方自述"能生成与主流工具都不一样的惊艳图像"。
   - **brainrender**(BrainGlobe)提供 `SHADER_STYLE` 预设:`default / metallic / plastic / shiny / glossy / ambient / off`,配合 `ROOT_ALPHA`、`ROOT_COLOR` 可调出"塑料感"或"金属感"的半透明大脑。
2. **半透明/玻璃质感 vs 实体封面**:透明脑壳叠加深部结构是解剖类图的主流画风(无头绪的"玻璃脑"),多用于显示深部核团、电极、纤维束。
3. **曲面 vs 体积**:皮层结果多用膨胀/扁平面 (inflated/flattened) 表面;深部结构多用体积渲染或 3D 网格 (mesh)。Surf Ice 支持 xray/切片滑块展示皮层下的深部对象。
4. **数据格式生态**:GIfTI/CIfTI/FreeSurfer (asc,srf,pial,w) / BrainNet NV / MZ3(Surf Ice 原生) / OBJ / STL / VTK / TRK / TCK 等。Surf Ice 与 BrainNet Viewer 兼容节点(脑区)与边 (edge) 文件,可直接互通网络图。
5. **可复现性趋势**:Aperture Neuro 2023 年综述 (_A Practical Guide for Generating Reproducible and Programmatic Neuroimaging Visualizations_) 建议从 GUI 手调转向**代码驱动出图**,并给出 R/Python/MATLAB 全工具对照表与代码模板生成器 (braincode),这是当前"科研画风"的最大趋势。

### 1.3 常用工具速览(按画风/能力)

| 工具 | 语言/环境 | 能力 | 画风要点 | 链接 |
|---|---|---|---|---|
| **Surf Ice** (MRIcroGL 姊妹项目) | 独立 GUI + 脚本 | 表面渲染、网状、纤维束、连接网络、图谱、统计图 | shader、环境光遮蔽、曲率阴影;"颜值天花板" | [neurolabusc/surf-ice](https://github.com/neurolabusc/surf-ice) |
| **BrainNet Viewer** | MATLAB GUI | 节点-边网络图、皮层/体积叠加 | 经典网络图画风,发文量大,节点 sphere + 边 tube | [NITRC](https://www.nitrc.org/projects/bnv/) |
| **brainrender** | Python (vedo/pyvista) | 任何注册到图谱坐标的数据:脑区、细胞、纤维、视频 | 半透明 + shader 风格;现代杂志封面风 | [brainglobe/brainrender](https://github.com/brainglobe/brainrender) |
| **nilearn** | Python | 玻璃脑、统计图、ROI、连接图、4D 图谱 | matplotlib 传统学术风,可投刊 | [nilearn](https://nilearn.github.io/) |
| **ENIGMA Toolbox** | Python/MATLAB | 皮层 + 16 个皮层下结构 (Desikan-Killiany) 3D 出图 (`plot_subcortical`) | 深部核团"独有"现成函数 | [ENIGMA toolbox](https://enigma-toolbox.readthedocs.io/) |
| **Brainspace / surfplot** | Python | 顶点/ROI 表面图,inflated | 白质表面 3D 图,主流 | [brainspace](https://brainspace.readthedocs.io/) |
| **PyCortex** | Python | 交互式网络浏览器可视化皮层 | 扁平皮层图 (flattened),web 交互 | [gallantlab/pycortex](https://github.com/gallantlab/pycortex) |
| **MNE-Python** | Python | 皮层表面 + EEG/MEG 源定位 + 连接 | 灰色皮层 + 彩色激活叠加,常用于头皮/皮层 | [mne-python](https://mne.tools/) |
| **FSLeyes** | Python GUI | 体积/表面/纤维束/网格/统计 | 交互可视化,质控友好 | [FSLeyes](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSLeyes) |
| **Freeview / FreeSurfer** | GUI (CLI 可脚本) | 全 neuroimaging;海马/杏仁核核团、丘脑核团、脑干分段 | 校正后 (recon-all) 结果的标准查看方式 | [freesurfer](https://surfer.nmr.mgh.harvard.edu/) |
| **Connectome Workbench** (wb_view) | GUI + CLI | HCP 数据、CIfTI、表面+体积、海马展开面 (HippUnfold 输出) | HCP 生态标准 | [workbench](https://www.humanconnectome.org/software/connectome-workbench) |
| **Neuroglancer** | Web (WebGL) | 任意切面 + 3D 网格 + 骨架;预计算/N5/Zarr/DVID/BOSS | 大数据在线浏览主流 | [google/neuroglancer](https://github.com/google/neuroglancer) |
| **NiiVue** | Web (WebGL2) | 30+ 格式体积/网格,移动端 | 轻量开源替代,非营利科研常用 | [niivue](https://niivue.com/) |
| **ITK-SNAP** | GUI | 手动分割、3D 轮廓渲染 | 分割任务标准工具 (ASHS 输出推荐查看器) | [itk-snap](http://www.itksnap.org/) |
| **3D Slicer** | GUI | 影像引导、体积渲染、DICOM | 临床/科研通用影像平台 | [slicer](https://www.slicer.org/) |
| **Aperture Neuro braincode** | 网页工具 | 自动生成 R/Python/MATLAB 出图代码模板 | 跟随评价:选新工具先看它 | [braincode](https://sidchop.shinyapps.io/braincode/) |

---

## 二、岛叶可视化工具与图谱

岛叶位于皮层深处,常需**球状膨胀/专门展开**或**单独提取 mask** 才能看清,主流依赖图谱 ROI 而非专用 GUI。

### 2.1 现成岛叶图谱/分割

| 图谱/工具 | 类型 | 岛叶划分 | 说明 |
|---|---|---|---|
| **Brainnetome Atlas (BNA)** | 连接为主图谱,246 区 | **INS-1 ~ INS-6** 六个亚区(hypergranular / vIa / dIa / vId/vIg / dIg / dId) | MPM 概率图 + 4D 概率图;提供 freesurfer/CIfTI 表面文件与 LUT 颜色表;有 MATLAB Viewer;中文团队 (CASIA) 产出 | [atlas.brainnetome.org](https://atlas.brainnetome.org/) |
| **Julich-Brain (JuBrain)** | 细胞结构概率图谱 (EBRAINS) | 岛叶后部 Ig1, Ig2, Id1(Kurth 2010);全图谱 200+ 区 | 概率图(10 例死后脑);SPM 工具箱 "JuBrain Anatomy Toolbox" 直接载入;siibra-explorer 在线浏览 + siibra-python 代码访问 | [julich-brain-atlas.de](https://julich-brain-atlas.de/atlas) |
| **MNI-insula 划区** | 岛叶专用分区 (Montreal) | 1 / 4 / 7 / 19 包层 (parcel) 多分辨率 | 用于 sEEG 岛叶有效连接研究(见下方 ft-insula),定义见该仓库 | [ins-amu/ft-insula](https://github.com/ins-amu/ft-insula) |
| **AAL / AAL2 / AAL3** | 全脑自动解剖标签 | AAL:Insula (33,34) | AAL3 (2020, Rolls 等) 增加丘脑核团、ACC 三分、NAcc、SN、VTA、红核、LC、中缝核等,与 MRIcron/SPM 配合 | [oxcns.org/aal3](https://www.oxcns.org/aal3.html) |
| **FreeSurfer 皮层重建** | 皮层表面 | 岛叶为皮层一部分(默认入皮层包层) | Surf Ice 文档提到:FreeSurfer 膨胀表面可"展开埋藏在脑沟中的岛叶",但注意 FreeSurfer 网格 ≠ MNI 空间,需重采样 | [FreeSurfer Wiki](https://surfer.nmr.mgh.harvard.edu/fswiki) |

### 2.2 岛叶相关研究仓库/管线

- **ft-insula**(ins-amu):人岛叶有效连接 (cortico-cortical evoked potentials),MNI-insula + Julich 两种划区 × Lausanne/ENIGMA 网格,基于 MNE 做皮层表面可视化 + ENIGMA 做皮层下网格可视化。可作为"岛叶专项可视化的标杆实现",含所有代码:https://github.com/ins-amu/ft-insula
- **ENIGMA Toolbox**:`plot_subcortical` 内建皮层下网格(含岛叶属皮层下层级的处理方案),与 ft-insula 配合。

### 2.3 岛叶显示技巧

- Surf Ice:加载 FreeSurfer 膨胀面可放大显示岛叶;或用 `Advanced > Convert voxelwise volume to mesh` 把岛叶 mask 转 3D 网格再叠加。
- 半透明皮层 + 岛叶实心高亮是主流做法(brainrender 的 `ROOT_ALPHA` + 独立 `add_brain_region`)。
- 用 AAL/BNA/Julich ROI 做 mask 后,在 nilearn `plot_roi` / `plot_stat_map` 中叠加切片展示。

---

## 三、边缘系统可视化工具与图谱

边缘系统(海马、杏仁核、扣带回、内嗅皮层等)是"亚区结构"最多的区域,需要**亚区分割 + 表面展开**类工具。

### 3.1 海马 + 杏仁核(最成熟)

| 工具 | 画风/能力 | 说明 |
|---|---|---|
| **FreeSurfer subregion segmentation** | 体素分割 + freeview 显示 | 海马亚区(CA1-4、DG、SRLM、hilus)、杏仁核核团(外侧/基底/副基底/中央/内侧/皮层/近层等, Saygin 2017);免 Matlab license 的 `segment_subregions hippo-amygdala --cross`(FS 7.3+ 整合);纵向支持;输出 `lh.hippoAmygLabels*.mgz` + 体积 CSV | [Wiki](https://surfer.nmr.mgh.harvard.edu/fswiki/HippocampalSubfieldsAndNucleiOfAmygdala) |
| **ASHS (Automatic Segmentation of Hippocampal Subfields)** | 多图谱分割 | 需要 T1 + 高分辨率斜冠 T2;UPENN-PMC 等图谱;输出建议用 ITK-SNAP 查看 3D 轮廓;可训练新结构 | [NITRC ASHS](https://www.nitrc.org/projects/ashs) |
| **HippUnfold** | **表面展开**(最"画风"特色) | BIDS App;U-Net 分割 → Laplace 坐标展开 → 拓扑约束亚区标签 → 生成 inner/midthickness/outer 海马表面 (GIfTI);支持扁平/展开显示;可用 Connectome Workbench、Freeview、HippUnfold Toolbox (Python/MATLAB) 绘图;eLife 2022 | [khanlab/hippunfold](https://github.com/khanlab/hippunfold), [HippUnfold 文档](https://hippunfold.khanlab.ca/) |
| **HippUnfold Toolbox** | 绘图/统计工具 | Python & MATLAB 函数:数据映射到展开面、厚度(gyrification)、亚区比较 | [jordandekraker/hippunfold_toolbox](https://github.com/jordandekraker/hippunfold_toolbox) |
| **AAL3** | 全脑标签 | ACC 分为 subgenual / pregenual / supracallosal 三部分(扣带回即边缘系统核心) | 见上文 |
| **Brainnetome Atlas** | 皮层亚区 | 边缘/扣带回、内嗅、海马体等皮层下亚区(36 个皮层下子区) | 见上文 |

### 3.2 海马/杏仁核可视化软件偏好

- **展开视图**:HippUnfold + Connectome Workbench 是"海马专属画风"(类似皮层展开图,能看到 CA 条带),Freeview 支持直接加载 `.gii` 曲面与 `.label.gii` 注释。
- **体积视图**:ITK-SNAP 叠 `_dseg.nii.gz` 看 3D 轮廓;Freeview 叠 `hippoAmygLabels.mgz` 看亚区。
- **3D 展示**:brainrender / Surf Ice 直接把 FreeSurfer 或 GIfTI 网格导入即可,`HippUnfold` 生成的 midthickness 面配上厚度色图非常出效果。

---

## 四、深部核团可视化工具与图谱

深部核团(基底节、丘脑、STN、SN、VTA、红核、丘底核等)可视化是 DBS 领域最成熟的方向,Lead-DBS 生态是"全家桶"。

### 4.1 一体化可视化平台

| 工具 | 载体 | 深部可视化能力 | 链接 |
|---|---|---|---|
| **Lead-DBS** | MATLAB | 电极定位重构、2D/3D 可视化、VTA 计算、纤维束追踪、**内置大量皮层下图谱**(DISTAL、AHEAD、CIT168、Chakravarty、Saranathan THOMAS、Harvard-Oxford、HybraPD、ATAG 等)+ 3D viewer + "DBS relevant structures" 预设 | [netstim/leaddbs](https://github.com/netstim/leaddbs) |
| **DISTAL 图谱** (Ewert 2017) | 图谱 | 专为 Lead-DBS 打造,精确对齐 ICBM 2009b MNI;基于组织学(Chakravarty)+ 连接组细分 STN/GPi 功能亚区(sensorimotor/associative/limbic);丘脑命名"罗塞塔石碑" | [DISTAL 文档](https://www.lead-dbs.org/helpsupport/knowledge-base/atlasesresources/distal-atlas/) |
| **CIT168 图谱** (Pauli 2018, Sci Data) | 概率图谱 | 高分辨率活体概率图谱,168 例;32 个结构双侧(label 表含 putamen/caudate/NAcc/extended amygdala/GPi/GPe/SNc/SNr/red nucleus/VTA/parabrachial pigmented/habenula/hypothalamus/mamillary/**STN**);提供 ICBM 2009c 1mm 版;**atlaskit** 配套工具 | [CIT168](https://github.com/jmtyszka/CIT168-SubCorticalAtlas), [Sci Data 论文](https://www.nature.com/articles/sdata201863) |
| **AHEAD 图谱** (Alkemade 2020) | 7T 多模态 | 亚毫米、>1000 个手工勾画的基底节概率图谱 | [Lead-DBS 图谱页](https://www.lead-dbs.org/helpsupport/knowledge-base/atlasesresources/atlases-2/) |
| **Saranathan THOMAS** (2021) | 丘脑专属 | 20 套 WMn-MPRAGE 手工分割 + 标签融合 -> 丘脑优化多图谱分割,丘脑精细分区 | 同上 |
| **HybraPD 图谱** | QSM+T1w | 87 例 PD;12 个双侧皮层下核团(含 GP 亚区、SN、STN) | 同上 |
| **AAL3** | 全脑 | 丘脑 15 核团细分 + NAcc + VTA + SN 致密/网状 + 红核 + LC + 中缝核 | 见上文 |
| **FreeSurfer** | 分割 | `aseg` 皮层下(尾状核、壳核、苍白球、杏仁核、海马、丘脑、脑干);`segment_subregions thalamus`(丘脑核团细分)、`brainstem` | [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/) |
| **ENIGMA Toolbox** | Python | `plot_subcortical` 一键 3D 显示 16 个皮层下结构(Desikan-Killiany) | [ENIGMA](https://enigma-toolbox.readthedocs.io/) |
| **JuBrain/Iglesias 概率丘脑图谱** | 体积 | 丘脑核团概率图,FS 7.3+ 整合;Iglesias et al. 2018 基于 ex vivo | 见 FreeSurfer |

### 4.2 深部核团"画风"特征

- **X-ray 半透明 + 深部实心高亮**:Surf Ice 专门有 "XRay sliders" 查看皮层下对象,可把 FSL/SPM 输出 meshify 后叠显。
- **DBS 电极 + VTA + 纤维束**:Lead-DBS 3D 场景是"深部核团临床画风"代表(电极板 + 激活体积 + 白质纤维)。
- **规范化 MNI 空间**:几乎所有深部图谱都有 MNI 版本;不同版本 (2009c NLIN asym) 需注意与 Lead-DBS 默认空间 (2009b) 差异。

---

## 五、综合选型建议

| 你的需求 | 推荐组合 |
|---|---|
| **快速看/质控**(任何脑区) | Freeview / FSLeyes / ITK-SNAP |
| **颜值最高的表面图**(皮层+深部叠加) | **Surf Ice**(shader + AO)或 **brainrender**(Python,可复现) |
| **发表级代码驱动出图** | nilearn (2D/玻璃脑) + brainrender/vedo (3D) + ENIGMA Toolbox (皮层下) |
| **岛叶专门分析** | Brainnetome (INS-1~6) 或 MNI-insula / Julich 划区;参考 ft-insula 管线(MNE + ENIGMA) |
| **海马/杏仁核亚区** | FreeSurfer `segment_subregions` 或 ASHS;要展开画风用 **HippUnfold** + Workbench |
| **深部核团/DBS** | **Lead-DBS** + DISTAL/CIT168/AHEAD/THOMAS 图谱 |
| **网络图**(节点-边) | BrainNet Viewer (经典) / Surf Ice (互通 Node/Edge 文件) / nilearn plot_connectome |
| **超大数据/在线分享** | Neuroglancer / NiiVue / siibra-explorer |
| **想快速选代码工具** | Aperture Neuro braincode 模板生成器 + 综述 Table 1 |

---

## 六、渲染引擎与优缺点详解

> 本节聚焦"每个工具**基于什么渲染引擎**、**有什么优缺点**"这一核心问题,并配以官方示例图(图片存于 `images/`,来源见各图注)。

### 6.1 渲染引擎谱系总览

| 引擎层 | 代表工具 | 说明 |
|---|---|---|
| **OpenGL + 可编程 shader**(桌面端原生) | Surf Ice, Connectome Workbench, FSLeyes | 性能最好、画风上限最高;FSLeyes/WB 还支持绕过 GPU 的离屏渲染 (OSMesa) 以便服务器出图 |
| **VTK(Visualization Toolkit)封装**(Python/MATLAB) | brainrender(v1/v2), ITK-SNAP 3D 窗口, MNE(经由 pyvista), 3D Slicer, BrainNet Viewer(间接) | 成熟、跨平台、丰富的 mesh/actor 管线;缺点是默认画风偏"工业风",需要 shader/样式定制才出大片感 |
| **WebGL / WebGL2 / WebGPU**(浏览器) | Neuroglancer, NiiVue, BrainBrowser, siibra-explorer | 零安装、可分享、支持超大体积数据 (GPU 纹理/分块加载);性能受浏览器限制 |
| **CIfTI / GIfTI 原生路径**(VDK 无关) | Connectome Workbench(原生), HippUnfold 表面 via wb_view | HCP 生态标准,支持 gray-ordinates、表面展开坐标 |
| **matplotlib / plotly 2D 图表层** | nilearn 大部分图, MNE 波形图, FSLeyes 的 Plot 面板, ENIGMA 统计图 | 出版级、可编辑、矢量输出;不适合真正的 3D 体积渲染 |

### 6.2 各工具详细对比

#### Surf Ice (Neurolabusc)

![Surf Ice 官方截图:皮层表面渲染,shader 环境光遮蔽效果](images/surfice_official.jpg)
*图:Surf Ice 官方 README 运行截图(Rorden, Nature Methods 2025)*

- **引擎**:自研 GLSL 渲染器(FreePascal/Lazarus 编写),OpenGL 3.3 Core、分支兼容 2.1;支持自定义 shader (`ao3_*.glsl` 等),环境光遮蔽 (ambient occlusion)、曲率阴影、体积转网格 (marching cubes)。
- **优点**:画风居于全生态顶端——官方自述"shader 生成与主流工具都不同的惊艳图像";轻量单文件分发;Python 脚本可批量出图;网络 (BrainNet .node/.edge)、纤维束 (tck/trk)、体积 (mgh/nii) 全能加载;与 MRIcroGL (体积渲染) 姊妹配对。
- **缺点**:GUI 交互选项多、新手学习曲线陡;骨骼网格格式 (mz3) 非标准,导出与其他工具互通需要转换;无统计分析管线(仅展示)。
- **适用**:发表级表面/网络/纤维束可视化;作为 MRIcroGL 的"表面渲染搭档"。

#### brainrender (BrainGlobe 生态)

![brainrender 示例:小鼠大脑半透明渲染 + 细胞点云(eLife 65751 Fig.3)](images/brainrender_example.jpg)
*图:Claudi et al. 2021, eLife 65751, Fig.3(CC-BY)*

- **引擎**:早期使用 `vtkplotter`/`vedo`,v2 依赖 `pyvista`(VTK 的 Python 封装)+ `trimesh`;场景由 BrainGlobe Atlas API 提供任意坐标空间。
- **优点**:几行代码出"杂志封图";`SHADER_STYLE` (`default/metallic/plastic/shiny/glossy/ambient`)+ `ROOT_ALPHA`/`ROOT_COLOR` 可精细控制半透明玻璃质感;与 atlas API 生态 (Allen、allen_human、atlas) 深度集成;支持动画/视频导出。
- **缺点**:体型小但依赖链深 (vedo/pyvista/pyxde 等),安装常见版本冲突;以"展示解剖 + 数据叠加"为主,数学分析能力弱;人类 MNI 空间 atlas 支持不如小鼠图谱完善(brainrender 起源于小鼠)。
- **适用**:论文 3D 示意图、封面图、神经解剖演示。

#### nilearn

![nilearn glass brain 示例:黑底玻璃脑风格](images/nilearn_glass_brain.png)
*图:nilearn 官方示例 `plot_demo_glass_brain.html`*

- **引擎**:`matplotlib` 为主(2D 切面、glass brain、ROI 叠加、connectome 圈图);表面图经 `surfplot`/matplotlib 3D;可选 plotly/ipyniivue 交互后端。
- **优点**:与 scikit-learn 全家桶无缝;glass brain/统计图是**神经科学论文出图事实标准**;矢量输出、颜色条、多面板支持完善;教程文档极其丰富 (sphinx-gallery)。
- **缺点**:3D 体积渲染不可用(nilearn 的 3D 是表面映射/半透明叠加,不做 ray-casting);画风偏"扁平学术风",美观度上限低于 Surf Ice/brainrender;大体积数据 (4D/万级卷) 交互性差。
- **适用**:fMRI 统计结果、ROI、连接组的论文 2D 图;科研流水线默认出图工具。

#### Connectome Workbench (wb_view)

- **引擎**:C++ 原生 + Qt5 GUI + OpenGL;`wb_command` CLI;OSMesa 支持离屏渲染(用于无显示器服务器出图)。
- **优点**:HCP/CIfTI 生态标准;gray-ordinate 表面-体积一体化;扁平/膨胀/无脑表面;`-show-scene` 可编程出图;渲染速度快、大数据友好。
- **缺点**:UI 老旧、交互反直觉;"snowing" 调色风格与现代审美脱节;学习成本高。
- **适用**:HCP 数据、亚皮层/皮层联合分析、HippUnfold 展开面查看。

#### FSLeyes

- **引擎**:wxPython + OpenGL;自研 `fsleyes.gl`(支持 GL 1.4/2.1/3.3);3D 视图用**体积光线投射 (ray-casting)**;Plot 面板走 matplotlib。
- **优点**:FSL 生态默认查看器;切面/光箱/3D 视图一键切换;管线可写 `fsleyes render` 离屏出图;open-GL 版本兼容极好(老显卡/虚拟机可用)。
- **缺点**:画风朴素(光线投射质感偏物理,不如 shader 渲染精致);功能堆叠导致菜单多。
- **适用**:临床/科研体素质控、FSL 处理结果查看。

#### ITK-SNAP

![ITK-SNAP 4.x 分割界面截图](images/itksnap_screenshot.png)
*图:ITK-SNAP 官网首页截图*

- **引擎**:Qt6 GUI + ITK 图像处理 + VTK 3D 渲染窗口;新版 3D 用 VTK,2D 切片渲染已替换为直接 OpenGL2 硬件渲染(更快)。
- **优点**:分割任务事实标准;自动 (active contour) + 手动分割;与 ASHS/HippUnfold 输出 (dseg.nii.gz) 直接配合;跨平台稳定。
- **缺点**:聚焦分割、不做统计/网络;画风功能化;渲染质量一般。
- **适用**:手动/半自动分割、亚区标签检查。

#### Freeview (FreeSurfer)

![FreeSurfer 海马/杏仁核亚区分割示例(freeview 查看)](images/freesurfer_hippo_amyg.png)
*图:FreeSurfer Wiki `HippocampalSubfieldsAndNucleiOfAmygdala`(Iglesias et al. 2015; Saygin et al. 2017)*

- **引擎**:Qt/C++ 自研 OpenGL 查看器;CLI 可脚本 (`freeview -v ...`)。
- **优点**:FreeSurfer 生态唯一权威查看器;海马/杏仁核/丘脑核团/脑干亚区分割可直接 LUT 显示;还原度高。
- **缺点**:仅与 FreeSurfer 输出深度绑定;对其他坐标空间 (MNI) 支持弱;视觉现代感不足。
- **适用**:FreeSurfer 结果查看与亚区分割可视化。

#### Lead-DBS

![Lead-DBS DISTAL 图谱:DBS 相关深部结构三维渲染](images/leaddbs_distal.png)
*图:Lead-DBS DISTAL atlas 知识库页面(经 lead-dbs.org 转载)*

- **引擎**:MATLAB 网格渲染(自研 3D viewer)+ SPM12 配准管线;图谱为 NIfTI。
- **优点**:深部核团生态最全:DISTAL、CIT168、AHEAD、THOMAS、HybraPD、ATAG 等;电极/VTA/纤维束一体化;预设视图 (DBS relevant structures)。
- **缺点**:MATLAB 依赖(需 32GB RAM + R2024b);重量级;渲染画风偏工程;非开放性。
- **适用**:DBS 电极定位、深部核团解剖可视化、连接组分析。

#### ENIGMA Toolbox

![ENIGMA Toolbox 皮层 + 皮层下 3D 渲染示例](images/enigma_toolbox.png)
*图:ENIGMA Toolbox 官方文档首页图 (MICA-MNI)*

- **引擎**:Python + matplotlib 3D;内嵌 Desikan-Killiany/Glasser/Schaefer 表面网格(FreeSurfer/GIfTI/VTK/OBJ);`plot_subcortical` 用预打包亚皮层网格。
- **优点**:`plot_subcortical` 是**现成的深部核团/皮层下整体渲染函数**;与疾病 meta 分析 (ENIGMA) 生态直接对接;教学文档完整。
- **缺点**:表面网格分辨率固定(非个体定制);3D 交互性一般。
- **适用**:大脑皮层 + 16 个皮层下结构一键出版图;ENIGMA 协议用户。

#### BrainNet Viewer

![BrainNet Viewer 网络图示例(节点-边可视化)](images/brainnet_viewer.png)
*图:BrainNet Viewer NITRC 截图(北京师范大学, Xan Mingrui)*

- **引擎**:MATLAB OpenGL 渲染 + 内嵌 NIfTI 表面/体积。
- **优点**:中国神经成像社区事实标准,发文量巨大;node/edge 简单文本格式,与 Surf Ice 互通;权重、颜色、粗细映射灵活。
- **缺点**:MATLAB 依赖;2019 年后停止更新;画风停留在 2010 年代。
- **适用**:脑网络(功能连接/重连)图、经典的"节点-连线"style。

#### HippUnfold

![HippUnfold:海马折叠-展开对比与亚区标签](images/hippunfold_subfields.png)
*图:HippUnfold GitHub README(DeKraker et al. 2022, eLife 77945)*

- **引擎**:底层是 nnU-Net (PyTorch) 分割 + Laplace 方程展开坐标系;表面处理经 Connectome Workbench 工具生成 GIfTI;输出可用 Freeview/ITK-SNAP/wb_view/HippUnfold Toolbox (Python/Matlab) 查看绘图。
- **优点**:唯一"展开坐标"系统,亚区分割拓扑一致;与 7T/ex vivo 图集 (BigBrain、Magdeburg) 对齐;FAIR (BIDS App)。
- **缺点**:只聚焦海马;安装复杂度高 (docker/snakemake);绘图功能需加装 toolbox。
- **适用**:海马亚区形态学/层状分析、海马"展开地图"可视化。

#### Neuroglancer

- **引擎**:纯前端 WebGL/WebGL2,Google 出品;支持 precomputed/Zarr/N5/DVID/BOSS 数据源;四窗格(3 正交切面 + 1 个 3D)。
- **优点**:超过 10 TB 体积数据浏览器内流畅浏览;零安装、URL 可分享(可做成长期公开链接);网格/骨架/分割着色丰富;生态大 (CloudVolume、TensorStore)。
- **缺点**:纯查看器(无统计编辑);画风偏"科技蓝"功能化;图片不主打"美学出版"。
- **适用**:超大分割数据、connectomics、公开数据集浏览。

#### NiiVue

- **引擎**:WebGL2(正在向 `niivue/mono` 重写,加 WebGPU);原生支持 30+ 体积/网格格式,含 DICOM/MINC/TIFF 插件;开源 (BSD),被 OpenNeuro、AFNI、FSL、Brainlife 等 50+ 项目采用。
- **优点**:跨平台(手机/平板/电脑);ihs 2D/3D 一体;与 FSL/FreeSurfer/ANTs 输出直接兼容;更新活跃。
- **缺点**:功能相对轻量(无分割编辑、无统计)。
- **适用**:网页版医学影像查看、数据共享、公开平台嵌入。

#### BrainBrowser

- **引擎**:three.js (WebGL),JS 库;Surface Viewer + Volume Viewer 两套。
- **优点**:嵌入简单(一个 HTTP 调用);需与 BrainInitiative 大数据配合 (CBRAIN)。
- **缺点**:活跃度下降;功能有限。
- **适用**:神经影像网站开发。

#### 3D Slicer / PyCortex / MNE-Python

- **3D Slicer**:VTK + Qt + ITK,临床/科研通用平台;几乎全能(分割、配准、体积渲染、引导手术),但画风"医用"、配置偏重。
- **PyCortex**:前端 three.js + 后端 numpy;支持**扁平皮层图 (flattened)** 交互,是"皮层展开地图"的网络呈现代表。
- **MNE-Python**:3D 后端 `pyvista`/`pyvistaqt`/`notebook`(可选 mayavi);皮层表面 + 头皮 + 源定位 + 时频一体化;画风现代(默认深色半透明),近年用 pyvista 后质感提升明显。

---

## 七、参考链接与文献

**综述与方法论文**
- Chopra S, Labache L, Dhamala E, Orchard ER, Holmes A. *A Practical Guide for Generating Reproducible and Programmatic Neuroimaging Visualizations*. Aperture Neuro, 2023. https://apertureneuro.org/article/85104-braincode-selector (含全工具对照表 + braincode 模板)
- Rorden C. *Surfice: visualizing neuroimaging meshes, tractography streamlines and connectomes*. Nature Methods, 2025. https://doi.org/10.1038/s41592-025-02764-6
- Claudi F, et al. *Visualizing anatomically registered data with Brainrender*. eLife, 2021. https://doi.org/10.7554/eLife.65751
- DeKraker J, et al. *Automated hippocampal unfolding for morphometry and subfield segmentation with HippUnfold*. eLife, 2022. https://doi.org/10.7554/eLife.77945
- Pauli W, Nili A, Tyszka M. *A high-resolution probabilistic in vivo atlas of human subcortical brain nuclei*. Scientific Data, 2018. https://doi.org/10.1038/sdata.2018.63
- Rolls ET, et al. *Automated anatomical labelling atlas 3 (AAL3)*. NeuroImage, 2020. https://www.oxcns.org/aal3.html
- Fan L, et al. *The Human Brainnetome Atlas*. NeuroImage, 2016. https://doi.org/10.1016/j.neuroimage.2016.03.027
- Amunts K, et al. *Julich-Brain: A 3D probabilistic atlas of the human brain's cytoarchitecture*. Science, 2020. https://julich-brain-atlas.de/
- Ewert S, et al. *Toward defining deep brain stimulation targets in MNI space: A subcortical atlas (DISTAL)*. NeuroImage, 2017. https://www.lead-dbs.org/helpsupport/knowledge-base/atlasesresources/distal-atlas/

**工具/图谱主页**
- Surf Ice: https://github.com/neurolabusc/surf-ice (NITRC: https://www.nitrc.org/projects/surfice/)
- brainrender / BrainGlobe: https://github.com/brainglobe/brainrender , https://brainglobe.info/
- Lead-DBS: https://github.com/netstim/leaddbs , 图谱库 https://www.lead-dbs.org/helpsupport/knowledge-base/atlasesresources/atlases-2/
- CIT168: https://github.com/jmtyszka/CIT168-SubCorticalAtlas , atlaskit https://github.com/jmtyszka/atlaskit
- Brainnetome: https://atlas.brainnetome.org/ , GitHub https://github.com/BrainnetomeAtlas/HUMAN-BRAINNETOME-ATLAS
- AAL3: https://www.oxcns.org/aal3.html
- JuBrain Anatomy Toolbox: https://github.com/inm7/jubrain-anatomy-toolbox ; Julich Brain Atlas https://julich-brain-atlas.de/atlas
- HippUnfold: https://github.com/khanlab/hippunfold ; 文档 https://hippunfold.khanlab.ca/
- ASHS: https://www.nitrc.org/projects/ashs
- ENIGMA Toolbox: https://enigma-toolbox.readthedocs.io/
- nilearn: https://nilearn.github.io/ ; Brainspace/surfplot: https://brainspace.readthedocs.io/
- PyCortex: https://github.com/gallantlab/pycortex ; MNE-Python: https://mne.tools/
- Neuroglancer: https://github.com/google/neuroglancer ; NiiVue: https://niivue.com/
- BrainNet Viewer: https://www.nitrc.org/projects/bnv/
- ft-insula (岛叶 sEEG 有效连接示范仓库): https://github.com/ins-amu/ft-insula
- FreeSurfer 海马/杏仁核核团分割: https://surfer.nmr.mgh.harvard.edu/fswiki/HippocampalSubfieldsAndNucleiOfAmygdala
