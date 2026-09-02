# -*- coding: utf-8 -*-
"""jellybrain.atlases: 内建图谱规格.

目前提供 Brainnetome Atlas 岛叶 (data_centers.json 亚区中心 +
subregion_func_network_Yeo_updated.csv 官方 Yeo-7 归属 +
AAL 岛叶 mask 作为真实形态来源).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .core import AtlasSpec, Subregion, YeoNetwork

# BNA 岛叶 12 亚区: 短名/全名/亚区体素中心/官方 Yeo-7
# 体素中心来自 BNA data_centers.json (站点坐标)
# Yeo-7 来自 subregion_func_network_Yeo_updated.csv (label 163-174)
#
# 注意: data_centers.json 右侧编号与左侧不镜像 (L1↔R2, L2↔R5, L3↔R4,
# L4↔R1, L5↔R6, L6↔R3 置换), 但官方网络/命名按索引对称 (L_1 与 R_1 均为 G).
# 因此右侧坐标用左侧镜像重建 (x_R = 183 - x_L, 经验验证 6 对均 ≤3mm),
# 保证几何/编号/网络三重左右对称.
BNA_INS_DATA = {
    'Ins_L_1': dict(short='G',      full='G · hypergranular',           vox=(54,131,105), yeo=YeoNetwork.SOMATOMOTOR),
    'Ins_L_2': dict(short='vIa',    full='vIa · ventral agranular',     vox=(54,118,99),  yeo=YeoNetwork.FRONTOPARIETAL),
    'Ins_L_3': dict(short='dIa',    full='dIa · dorsal agranular',      vox=(53,123,119), yeo=YeoNetwork.VENTRAL_ATTENTION),
    'Ins_L_4': dict(short='vId/vIg', full='vId/vIg · ventral dysgranular/granular', vox=(56,106,98), yeo=YeoNetwork.VENTRAL_ATTENTION),
    'Ins_L_5': dict(short='dIg',    full='dIg · dorsal granular',       vox=(59,141,122), yeo=YeoNetwork.SOMATOMOTOR),
    'Ins_L_6': dict(short='dId',    full='dId · dorsal dysgranular',    vox=(57,143,107), yeo=YeoNetwork.VENTRAL_ATTENTION),
    # 右侧 = 左侧镜像 (x_R = 183 - x_L, y/z 不变)
    'Ins_R_1': dict(short='G',      full='G · hypergranular',           vox=(129,131,105), yeo=YeoNetwork.SOMATOMOTOR),
    'Ins_R_2': dict(short='vIa',    full='vIa · ventral agranular',     vox=(129,118,99),  yeo=YeoNetwork.FRONTOPARIETAL),
    'Ins_R_3': dict(short='dIa',    full='dIa · dorsal agranular',      vox=(130,123,119), yeo=YeoNetwork.VENTRAL_ATTENTION),
    'Ins_R_4': dict(short='vId/vIg', full='vId/vIg · ventral dysgranular/granular', vox=(127,106,98), yeo=YeoNetwork.VENTRAL_ATTENTION),
    'Ins_R_5': dict(short='dIg',    full='dIg · dorsal granular',       vox=(124,141,122), yeo=YeoNetwork.SOMATOMOTOR),
    'Ins_R_6': dict(short='dId',    full='dId · dorsal dysgranular',    vox=(126,143,107), yeo=YeoNetwork.VENTRAL_ATTENTION),
}


def _aal_insula_mask_data():
    """加载 AAL 岛叶 mask 数据 (nilearn 缓存)."""
    from nilearn import image, datasets
    a = datasets.fetch_atlas_aal(version='SPM12')
    img = image.load_img(a['maps'])
    data = np.asarray(img.get_fdata())
    names = a['labels']
    idxs = a['indices']
    mask = np.zeros_like(data, dtype=bool)
    for i, n in enumerate(names):
        if 'Insula' in str(n):
            mask |= (np.round(data) == float(idxs[i]))
    return mask, img


def _insula_mask_fn():
    mask, _ = _aal_insula_mask_data()
    return mask


def _insula_affine_fn():
    _, img = _aal_insula_mask_data()
    return img.affine


def bna_insula_spec() -> AtlasSpec:
    """Brainnetome Atlas 岛叶 12 亚区规格."""
    # 先计算各亚区 MNI 中心 (与 scripts.insula_morph.bna_centers_mni 一致)
    from nilearn import image, datasets
    a = datasets.fetch_atlas_aal(version='SPM12')
    img = image.load_img(a['maps'])
    data = np.asarray(img.get_fdata())
    names = a['labels']
    idxs = a['indices']
    mask = np.zeros_like(data, dtype=bool)
    for i, n in enumerate(names):
        if 'Insula' in str(n):
            mask |= (np.round(data) == float(idxs[i]))
    coords = np.argwhere(mask)
    aff = img.affine
    mm = (aff[:3, :3] @ coords.T).T + aff[:3, 3]
    left, right = mm[mm[:, 0] < 0], mm[mm[:, 0] > 0]
    rm_l = left.mean(axis=0)
    rs_l = np.array([left[:, i].std() for i in range(3)])
    rm_r = right.mean(axis=0)
    rs_r = np.array([right[:, i].std() for i in range(3)])

    allb = np.array([d['vox'] for d in BNA_INS_DATA.values()], dtype=float)
    bm, bs = allb.mean(axis=0), allb.std(axis=0)

    subregions: List[Subregion] = []
    for key, d in BNA_INS_DATA.items():
        v = np.array(d['vox'], dtype=float)
        vn = (v - bm) / bs
        is_left = key.startswith('Ins_L')
        rm, rs = (rm_l, rs_l) if is_left else (rm_r, rs_r)
        x = rm[0] + vn[0] * rs[0] * 0.02
        y = rm[1] + vn[1] * rs[1] * 0.6
        z = rm[2] + vn[2] * rs[2] * 0.6
        # 唯一 name (L/R 前缀) 供 Voronoi 分区; full_name/short 供展示
        subregions.append(Subregion(
            name=f'{key}',  # Ins_L_1 ... Ins_R_6 (唯一)
            full_name=d['full'],
            short=d['short'],
            mni_center=np.array([x, y, z]), yeo7=d['yeo']))
    return AtlasSpec(
        atlas_name='brainnetome',
        region_name='insula',
        subregions=subregions,
        region_mask_fn=_insula_mask_fn,
        region_mask_affine_fn=_insula_affine_fn,
    )


def get_spec(atlas: str, region: str = 'insula') -> AtlasSpec:
    """按图谱名 + 脑区名取规格. atlas='brainnetome'."""
    if atlas.lower() == 'brainnetome':
        if region.lower() == 'insula':
            return bna_insula_spec()
        raise ValueError(f'brainnetome 暂仅提供 insula, 收到 {region!r}')
    raise ValueError(f'未知图谱 {atlas!r}, 目前只有 brainnetome')
