# -*- coding: utf-8 -*-
"""在 trame viewer HTML 注入自定义导出工具栏 (PNG/PDF/TIF).

利用 trame-vtk viewer 的 canvas + captureImages API:
  - 导出 PNG: 当前视角 canvas 截图
  - 导出 PDF: PNG -> jsPDF (CDN)
  - 导出 TIF: PNG -> tiff-js (CDN)
注入点: </body> 之前.
"""
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

INJECT_JS = r"""
<script>
/* ================= jellybrain 导出工具栏 + DOM 标签 ================= */
(function() {
  // ---------- 亚区标签配置 (名称 + 网络色) ----------
  // [x, y, z] 为亚区世界坐标 (MNI mm, 近似屏幕投影), 名称, 颜色
    var SUBREGIONS = window.JB_SUBREGIONS || [];
  function subInjected() {
    if (!SUBREGIONS.length) return;
    var canv = document.querySelector('#vtk-root canvas, canvas');
    if (!canv) return;
    var w = window.innerWidth, h = window.innerHeight;
    var placed = [];
    SUBREGIONS.forEach(function(sr) {
      var el = document.createElement('div');
      el.className = 'jb-label';
      el.textContent = sr[3];
      // 纯色简约: Arial, 纯色底板, 无阴影/渐变/边框
      el.style.cssText =
        'position:fixed;z-index:9998;transform:translate(-50%,-50%);' +
        'padding:4px 10px;border-radius:3px;' +
        'font:600 13px Arial, "Helvetica Neue", sans-serif;' +
        'background:' + sr[4] + ';color:' + sr[5] + ';' +
        'white-space:nowrap;letter-spacing:.3px;';
      document.body.appendChild(el);
      var p = projectPoint(sr[0], sr[1], sr[2], w, h);
      // 防重叠: 检测与已放置标签矩形碰撞, 向下/右微移
      var ew = el.offsetWidth, eh = el.offsetHeight;
      var lx = p.x, ly = p.y;
      var tries = 0;
      while (placed.some(function(r) {
        return Math.abs(lx - r.x) < (ew + r.w) / 2 + 6 &&
               Math.abs(ly - r.y) < (eh + r.h) / 2 + 4;
      })) {
        lx += 6; ly += 24;
        if (++tries > 40) break;
      }
      placed.push({x: lx, y: ly, w: ew, h: eh});
      el.style.left = lx + 'px';
      el.style.top = ly + 'px';
      el.dataset.x = sr[0]; el.dataset.y = sr[1]; el.dataset.z = sr[2];
    });
    var el = document.createElement('style');
    el.textContent = '.jb-label:hover{filter:brightness(1.1)}' +
      '.jb-label{user-select:none}';
    document.head.appendChild(el);
  }

  // 透视投影: 世界坐标 -> 屏幕 (精确, 与 vtk 透视相机一致)
  // fov=30° (pyvista 默认), zoom 影响实际 fov: tan(fov/2)/zoom
  var CAM = window.JB_CAM || null;
  var FOV_HALF_TAN = Math.tan((30 / 2) * Math.PI / 180);  // 0.2679
  var ZOOM = 1.0;
  function projectPoint(x, y, z, w, h) {
    var pos = CAM ? CAM.pos : [280, -280, 240];
    var foc = CAM ? CAM.foc : [0, 0, 5];
    var upv = CAM ? CAM.up : [0, 0, 1];
    var vx = foc[0] - pos[0], vy = foc[1] - pos[1], vz = foc[2] - pos[2];
    var vl = Math.sqrt(vx * vx + vy * vy + vz * vz);
    vx /= vl; vy /= vl; vz /= vl;
    // r = up x v (右), u = v x r (上)
    var rx = upv[1] * vz - upv[2] * vy, ry = upv[2] * vx - upv[0] * vz,
        rz = upv[0] * vy - upv[1] * vx;
    var ul = Math.sqrt(rx * rx + ry * ry + rz * rz) || 1;
    rx /= ul; ry /= ul; rz /= ul;
    var ux = vy * rz - vz * ry, uy = vz * rx - vx * rz, uz = vx * ry - vy * rx;
    var dx = x - pos[0], dy = y - pos[1], dz = z - pos[2];
    var cx = dx * rx + dy * ry + dz * rz;
    var cy = dx * ux + dy * uy + dz * uz;
    var cz = dx * vx + dy * vy + dz * vz;   // 深度
    if (cz <= 1) cz = 1;
    var tanf = FOV_HALF_TAN / ZOOM;
    var sxp = (cx / cz) / tanf * (h / 2);
    var syp = (cy / cz) / tanf * (h / 2);
    return {x: w / 2 + sxp, y: h / 2 - syp, depth: cz};
  }

  function waitForViewer(cb, tries) {
    tries = tries || 0;
    var canv = document.querySelector('#vtk-root canvas, canvas');
    if (canv) { cb(); return; }
    if (tries > 200) return;
    setTimeout(function() { waitForViewer(cb, tries + 1); }, 250);
  }

  function addToolbar() {
    var bar = document.createElement('div');
    bar.id = 'jb-toolbar';
    bar.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;' +
      'background:#ffffffcc;padding:8px 10px;border-radius:8px;' +
      'box-shadow:0 2px 8px rgba(0,0,0,.2);font:13px sans-serif;';
    bar.innerHTML =
      '<b>导出当前视角</b> &nbsp;' +
      '<button id="jb-png">PNG</button> ' +
      '<button id="jb-pdf">PDF</button> ' +
      '<button id="jb-tif">TIF</button>' +
      '&nbsp;<span id="jb-hint" style="color:#888"></span>';
    document.body.appendChild(bar);

    var hint = document.getElementById('jb-hint');
    function snap() {
      var canv = document.querySelector('#vtk-root canvas, canvas');
      if (!canv) { hint.textContent = '未找到画布'; return null; }
      return canv;
    }
    function download(blob, name) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      setTimeout(function() { URL.revokeObjectURL(a.href); }, 1000);
    }
    function toBlob(canv, mime, cb) {
      if (canv.toBlob) { canv.toBlob(cb, mime); }
      else { cb(null); }
    }

    document.getElementById('jb-png').onclick = function() {
      var c = snap(); if (!c) return;
      toBlob(c, 'image/png', function(b) {
        if (b) download(b, 'insula_view.png');
        else hint.textContent = '导出失败';
      });
    };
    document.getElementById('jb-pdf').onclick = function() {
      var c = snap(); if (!c) return;
      if (!window.jspdf && !window.jsPDF) {
        var s = document.createElement('script');
        s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
        s.onload = function() { pdfExport(c); };
        document.head.appendChild(s);
      } else pdfExport(c);
      function pdfExport(canv) {
        var J = window.jspdf ? window.jspdf.jsPDF : window.jsPDF;
        var img = canv.toDataURL('image/png');
        var w = canv.width, h = canv.height;
        var pdf = new J('p', 'px', [w, h]);
        pdf.addImage(img, 'PNG', 0, 0, w, h);
        pdf.save('insula_view.pdf');
      }
    };
    document.getElementById('jb-tif').onclick = function() {
      var c = snap(); if (!c) return;
      if (!window.TIFF) {
        var s = document.createElement('script');
        s.src = 'https://cdnjs.cloudflare.com/ajax/libs/tiff/0.1.2/tiff.min.js';
        s.onload = function() { tifExport(c); };
        document.head.appendChild(s);
      } else tifExport(c);
      function tifExport(canv) {
        var img = canv.toDataURL('image/png');
        var imgEl = new Image();
        imgEl.onload = function() {
          var c2 = document.createElement('canvas');
          c2.width = imgEl.width; c2.height = imgEl.height;
          c2.getContext('2d').drawImage(imgEl, 0, 0);
          var tiff = new window.TIFF();
          var ifd = new window.TIFF.ImageIFD(c2.width, c2.height);
          var ctx = c2.getContext('2d');
          var data = ctx.getImageData(0, 0, c2.width, c2.height).data;
          ifd.width = c2.width; ifd.height = c2.height;
          ifd.bitsPerSample = [8, 8, 8];
          ifd.samplesPerPixel = 3;
          ifd.photometricInterpretation = 2;
          ifd.stripOffsets = [0];
          ifd.rowsPerStrip = c2.height;
          ifd.stripByteCounts = [data.length];
          ifd.data = data;
          var buf = tiff.encodeDirectory(ifd);
          var arr = new Uint8Array(buf);
          var blob = new Blob([arr], {type: 'image/tiff'});
          download(blob, 'insula_view.tif');
        };
        imgEl.src = img;
      }
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addToolbar);
  } else {
    addToolbar();
  }
  waitForViewer(subInjected);
})();
</script>
"""


def inject_toolbar(html_path: str, out_path: str = None,
                   subregions=None):
    """注入导出工具栏 + DOM 标签 into trame viewer HTML.

    subregions: 可选 [(x,y,z, label, color_hex, text_color), ...]
    """
    import numpy as np
    html = open(html_path, 'r', encoding='utf-8').read()

    # 构建亚区 JS 数据
    js_data = 'window.JB_SUBREGIONS = [];'
    if subregions:
        items = []
        for sr in subregions:
            x, y, z, lbl, color, text = sr
            items.append(f'[{x},{y},{z},"{lbl}","{color}","{text}"]')
        js_data = 'window.JB_SUBREGIONS = [' + ','.join(items) + '];'

    inject = f'<script>{js_data}</script>\n' + INJECT_JS
    html = html.replace('</body>', inject + '\n</body>')
    out = out_path or html_path
    open(out, 'w', encoding='utf-8').write(html)
    print('injected ->', out)
    return out


if __name__ == '__main__':
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(__file__), '..', '..', 'images',
                     'insula_viewer.html')
    dst = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(src), 'insula_viewer_exports.html')

    # 从 jellybrain spec 生成亚区标签数据 (坐标/名称/网络色)
    subregions = None
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from jellybrain import atlases
        from jellybrain.core import YeoNetwork
        spec = atlases.get_spec('brainnetome', 'insula')
        subregions = []
        for s in spec.subregions:
            rgb = YeoNetwork.RGB[s.yeo7 - 1]
            lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            text = '#FFFFFF' if lum < 0.55 else '#202020'
            shape = '#%02X%02X%02X' % tuple(int(v * 255) for v in rgb)
            c = s.mni_center
            lbl = f'{s.short} · {s.name}' if s.short else s.name
            subregions.append((float(c[0]), float(c[1]), float(c[2]),
                               lbl, shape, text))
        print(f'label data: {len(subregions)} subregions')
    except Exception as e:
        print('spec load failed, no labels:', e)

    inject_toolbar(src, dst, subregions)
