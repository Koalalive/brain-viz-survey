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
6. [参考链接与文献](#六参考链接与文献)

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

## 六、参考链接与文献

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
