# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\29698\brain-viz-survey\scripts')
import numpy as np
from jelly_insula import aal_insula_mm, register_bna
aal = aal_insula_mm()
left = aal[aal[:,0]<0]; right = aal[aal[:,0]>0]
print('AAL center L:', np.round(left.mean(axis=0),1), 'R:', np.round(right.mean(axis=0),1))
pts = register_bna()
for k,v in pts.items():
    print(k, np.round(v,1))
