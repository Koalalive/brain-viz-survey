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
    // ---------- 亚区标签: DOM 层 (纯文字无气泡, 黑字白描边, 跟随旋转) ----------
  // vtkTextActor3D 在 vtk.js 导出不渲染, 故用 DOM + worldToDisplay 投影 (跟随旋转).
  var SUBREGIONS = window.JB_SUBREGIONS || [];
  var DOM_LABELS = [];
  function getVtkView() {
    var OLV = window.OfflineLocalView;
    if (!OLV) return null;
    // 多次尝试: OfflineLocalView 实例属性
    for (var k in OLV) {
      if (OLV[k] && typeof OLV[k] === 'object' && OLV[k].worldToDisplay) {
        return OLV[k];
      }
    }
    return null;
  }
  function worldToScreen(pt, w, h) {
    var view = getVtkView();
    if (view && view.worldToDisplay) {
      try {
        var out = view.worldToDisplay(pt);
        if (out) {
          return {x: out[0], y: h - out[1], depth: out[2]};
        }
      } catch (e) {}
    }
    // fallback: 数学投影
    var p = projectPoint(pt[0], pt[1], pt[2], w, h);
    return {x: p.x, y: p.y, depth: p.depth};
  }
  function updateDomLabels() {
    if (!DOM_LABELS.length) return;
    var w = window.innerWidth, h = window.innerHeight;
    var placed = [];
    DOM_LABELS.forEach(function(l) {
      var p = worldToScreen([l.wx, l.wy, l.wz], w, h);
      // 防重叠: 与已布置标签碰撞则向下错开
      var lx = p.x, ly = p.y;
      var ew = l.el.offsetWidth || 40, eh = l.el.offsetHeight || 16;
      var tries = 0;
      while (placed.some(function(r) {
        return Math.abs(lx - r.x) < (ew + r.w) / 2 + 4 &&
               Math.abs(ly - r.y) < (eh + r.h) / 2 + 3;
      })) {
        ly += 22;
        if (++tries > 25) break;
      }
      placed.push({x: lx, y: ly, w: ew, h: eh});
      l.el.style.left = lx + 'px';
      l.el.style.top = ly + 'px';
    });
  }
  function subInjected() {
    if (!SUBREGIONS.length) return;
    var canv = document.querySelector('#vtk-root canvas, canvas');
    if (!canv) return;
    SUBREGIONS.forEach(function(sr) {
      var el = document.createElement('div');
      el.className = 'jb-label';
      el.textContent = sr[3];
      // 纯文字无气泡: 黑字 + 白描边 (可读性), 无底板
      el.style.cssText =
        'position:fixed;z-index:9998;transform:translate(-50%,-50%);' +
        'font:700 14px Arial, "Helvetica Neue", sans-serif;' +
        'color:#000;text-shadow:-1px -1px 0 #fff,1px -1px 0 #fff,' +
        '-1px 1px 0 #fff,1px 1px 0 #fff,0 0 3px #fff;' +
        'white-space:nowrap;user-select:none;pointer-events:none;';
      document.body.appendChild(el);
      DOM_LABELS.push({el: el, wx: sr[0], wy: sr[1], wz: sr[2]});
    });
    var lastT = 0;
    function tick() {
      var now = Date.now();
      if (now - lastT > 150) { updateDomLabels(); lastT = now; }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    ["mouseup", "touchend", "wheel", "mousemove"].forEach(function(ev) {
      window.addEventListener(ev, function() { updateDomLabels(); }, true);
    });
    if (!window.__jb_legend_added) {
      window.__jb_legend_added = true;
      add_legend_panel();
    }
  }

  // ---------- 图例面板 (Yeo-7 色卡, 可折叠) ----------
  function add_legend_panel() {
    var leg = document.createElement('div');
    leg.id = 'jb-legend';
    leg.style.cssText =
      'position:fixed;bottom:12px;right:12px;z-index:9998;' +
      'background:#ffffffee;padding:10px 14px;border-radius:8px;' +
      'box-shadow:0 1px 4px rgba(0,0,0,.15);font:13px Arial,sans-serif;';
    var items = [
      ['Visual', '#781286'], ['Somatomotor', '#4682B4'],
      ['Dorsal Attention', '#00760E'], ['Ventral Attention', '#C43AFA'],
      ['Limbic', '#DCF8A4'], ['Frontoparietal', '#E69422'],
      ['Default Mode', '#CD3E4E']];
    var html = '<div style="font-weight:700;margin-bottom:6px">' +
      'Yeo-7 Networks <span id="jb-leg-toggle" style="cursor:pointer;' +
      'color:#888;font-size:11px">[-]</span></div>';
    items.forEach(function(it) {
      html += '<div style="display:flex;align-items:center;' +
        'margin:3px 0;color:#333">' +
        '<span style="display:inline-block;width:16px;height:16px;' +
        'border-radius:3px;margin-right:8px;background:' + it[1] + '"></span>' +
        it[0] + '</div>';
    });
    leg.innerHTML = html;
    document.body.appendChild(leg);
    var t = document.getElementById('jb-leg-toggle');
    t.onclick = function() {
      var body = leg.innerHTML;
      if (leg.dataset.collapsed) {
        add_legend_panel(); leg.dataset.collapsed = '';
      } else {
        leg.innerHTML = '<div style="font-weight:700;color:#333">' +
          'Yeo-7 Networks <span id="jb-leg-toggle" style="cursor:pointer;' +
          'color:#888;font-size:11px">[+]</span></div>';
        leg.dataset.collapsed = '1';
        document.getElementById('jb-leg-toggle').onclick =
          leg.querySelector('span').onclick = function(){ add_legend_panel(); };
      }
    };
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
      '&nbsp;|&nbsp;图例右下角可折叠' +
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
      var img = c.toDataURL('image/jpeg', 0.95);
      var jpeg = atob(img.split(',')[1]);
      var jlen = jpeg.length;
      var w = c.width, h = c.height;
      var objects = [];
      objects.push('<< /Type /Catalog /Pages 2 0 R >>');
      objects.push('<< /Type /Pages /Kids [3 0 R] /Count 1 >>');
      objects.push('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + w + ' ' + h +
                   '] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>');
      objects.push('<< /Type /XObject /Subtype /Image /Width ' + w +
                   ' /Height ' + h + ' /ColorSpace /DeviceRGB /BitsPerComponent 8' +
                   ' /Filter /DCTDecode /Length ' + jlen + ' >>\nstream\n' +
                   jpeg + '\nendstream');
      var stream = 'q ' + w + ' 0 0 ' + h + ' 0 0 cm /Im0 Do Q';
      objects.push('<< /Length ' + stream.length + ' >>\nstream\n' +
                   stream + '\nendstream');
      var pdf = '%PDF-1.4\n';
      var offsets = [];
      for (var i = 0; i < objects.length; i++) {
        offsets.push(pdf.length);
        pdf += (i + 1) + ' 0 obj\n' + objects[i] + '\nendobj\n';
      }
      var xrefPos = pdf.length;
      pdf += 'xref\n0 ' + (objects.length + 1) + '\n0000000000 65535 f \n';
      offsets.forEach(function(o) {
        pdf += ('0000000000' + o).slice(-10) + ' 00000 n \n';
      });
      pdf += 'trailer\n<< /Size ' + (objects.length + 1) + ' /Root 1 0 R >>\n' +
             'startxref\n' + xrefPos + '\n%%EOF';
      download(new Blob([pdf], {type: 'application/pdf'}), 'insula_view.pdf');
    };
    document.getElementById('jb-tif').onclick = function() {
      var c = snap(); if (!c) return;
      // WebGL canvas: 用 toDataURL -> 2D canvas (保证可读像素)
      var imgEl = new Image();
      imgEl.onload = function() {
        var c2 = document.createElement('canvas');
        c2.width = imgEl.width; c2.height = imgEl.height;
        var ctx = c2.getContext('2d');
        ctx.drawImage(imgEl, 0, 0);
        var imgData = ctx.getImageData(0, 0, c2.width, c2.height).data;
        var w = c2.width, h = c2.height;
        var rowBytes = w * 3;
        var stripLen = rowBytes * h;
        // 最小标准 TIFF: 8 header + 2 count + 14*12 entries + 4 nextIFD
        var data = new Uint8Array(8 + 2 + 14 * 12 + 4 + stripLen);
        var dv = new DataView(data.buffer);
        data[0] = 0x49; data[1] = 0x49; data[2] = 42; data[3] = 0;
        dv.setUint32(4, 8, true);          // IFD offset = 8
        var ifd = 8;
        dv.setUint16(ifd, 14, true);       // entry count = 14
        var e = ifd + 2;
        var dataStart = ifd + 2 + 14 * 12 + 4;
        function w16(off, v) { dv.setUint16(off, v, true); }
        function w32(off, v) { dv.setUint32(off, v, true); }
        // 写条目: 所有 count=1 直接把值放 offset 字段 (SHORT 低16位)
        function E(tag, type, count, value) {
          w16(e, tag); w16(e + 2, type); w32(e + 4, count);
          if (type === 3 && count === 1) {
            w16(e + 8, value); w16(e + 10, 0);
          } else {
            w32(e + 8, value);
          }
          e += 12;
        }
        E(256, 4, 1, w);              // ImageWidth
        E(257, 4, 1, h);              // ImageLength
        E(258, 3, 1, 8);              // BitsPerSample = 8 (单值, RGB 共用)
        E(259, 3, 1, 1);              // Compression = none
        E(262, 3, 1, 2);              // Photometric = RGB
        E(273, 4, 1, dataStart);      // StripOffsets
        E(277, 3, 1, 3);              // SamplesPerPixel = 3
        E(278, 4, 1, h);              // RowsPerStrip
        E(279, 4, 1, stripLen);       // StripByteCounts
        E(282, 3, 1, 72);             // XResolution (SHORT 近似)
        E(283, 3, 1, 72);             // YResolution
        E(284, 3, 1, 1);              // PlanarConfig = 1
        E(296, 3, 1, 2);              // ResolutionUnit = inch
        E(305, 2, 1, 0);              // Software (空)
        w32(ifd + 2 + 14 * 12, 0);    // next IFD = 0
        for (var i = 0; i < h; i++) {
          for (var x = 0; x < w; x++) {
            var src = (i * w + x) * 4;
            var dst = dataStart + i * rowBytes + x * 3;
            data[dst] = imgData[src];
            data[dst + 1] = imgData[src + 1];
            data[dst + 2] = imgData[src + 2];
          }
        }
        download(new Blob([data], {type: 'image/tiff'}), 'insula_view.tif');
      };
      imgEl.src = c.toDataURL('image/png');
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
