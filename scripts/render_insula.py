# -*- coding: utf-8 -*-
"""生成岛叶亚区可视化示意参考图(基于 nilearn + AAL 图谱,原创可复现)。"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import nibabel as nib
from nilearn import plotting, datasets, image

# 1. AAL 图谱 (含岛叶 33=左, 34=右)
atlas = datasets.fetch_atlas_aal(version="SPM12")
maps = atlas["maps"]  # Nifti image 切片
labels = atlas["indices"]
names = atlas["labels"]

# AAL 标签: 33=Insula L, 34=Insula R (AAL3 中编号不变)
# 从 label list 找 insula index
ins_idx = [i for i, n in enumerate(names) if "Insula" in str(n)]
print("insula labels:", [(names[i], labels[i]) for i in ins_idx])

atl_img = image.load_img(maps)
data = atl_img.get_fdata()

# 构造 insula mask (label 33/34)
mask = np.zeros_like(data)
for i in ins_idx:
    lab = int(labels[i])
    mask[data == lab] = 1

# 与 T1 模板叠加: 用 nilearn 自带 MNI 模板
from nilearn.datasets import load_mni152_template
template = load_mni152_template()

# 转成 stat map
ins_img = nib.Nifti1Image(mask, atl_img.affine, atl_img.header)

OUT = "C:/Users/29698/brain-viz-survey/images/"

fig1 = plotting.plot_stat_map(
    ins_img, bg_img=template, display_mode="ortho", cut_coords=(0, -14, 6),
    colorbar=False, title="AAL Insula (33/34) on MNI152", cmap="coolwarm",
    threshold=0.5,
)
fig1.savefig(OUT + "insula_aal_slices.png", dpi=200)
fig1.close()

# 2. 3D 半球视图: glass brain 填充大脑显示岛叶位置
fig2 = plotting.plot_glass_brain(
    ins_img, display_mode="lzry", colorbar=False,
    title="AAL Insula - Glass Brain", cmap="RdBu_r", threshold=0.5,
)
fig2.savefig(OUT + "insula_aal_glass.png", dpi=200)
fig2.close()

# 3. 矢状/冠状切片近观 (右岛叶)
fig3 = plotting.plot_stat_map(
    ins_img, bg_img=template, display_mode="x", cut_coords=(38,),
    colorbar=False, title="Right Insula - Sagittal", cmap="coolwarm", threshold=0.5,
)
fig3.savefig(OUT + "insula_aal_sag.png", dpi=200)
fig3.close()

print("done: 3 figures saved")
