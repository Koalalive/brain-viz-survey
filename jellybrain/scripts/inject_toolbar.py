# -*- coding: utf-8 -*-
"""inject_toolbar 重写: 截图走 renderWindow.captureImages, 标签投影走相机矩阵.

核心改动:
  1. 截图:    window.global.renderWindow.captureImages('image/png') -> dataURL
              (修复 PDF 空白: canvas.toDataURL 在 WebGL 上为空白, captureImages 走 vtk 管线)
  2. 标签跟随: renderer.getActiveCamera() 的 getViewMatrix + getProjectionMatrix
              手算 worldToDisplay, 每 150ms 刷新 -> 旋转时标签跟随.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

INJECT_JS = r"""
<script>
/* ================= jellybrain 导出工具栏 + 标签投影 (via renderWindow) ================= */
(function() {
  var SUBREGIONS = window.JB_SUBREGIONS || [];
  var DOM_LABELS = [];
  var CAM_INIT = window.JB_CAM || null;   // {pos:.., focal:.., up:..}

  function getRW() {
    return (window.global && window.global.renderWindow) ? window.global.renderWindow : null;
  }
  function getCam() {
    var rw = getRW();
    if (!rw) return null;
    var ren = rw.getRenderers && rw.getRenderers()[0];
    return ren ? ren.getActiveCamera() : null;
  }
  function applyInitCam() {
    if (!CAM_INIT) return;
    var cam = getCam();
    if (!cam) return;
    try {
      cam.setPosition(CAM_INIT.pos[0], CAM_INIT.pos[1], CAM_INIT.pos[2]);
      cam.setFocalPoint(CAM_INIT.focal[0], CAM_INIT.focal[1], CAM_INIT.focal[2]);
      cam.setViewUp(CAM_INIT.up[0], CAM_INIT.up[1], CAM_INIT.up[2]);
      cam.setClippingRange(CAM_INIT.clip[0], CAM_INIT.clip[1]);
    } catch (e) {
      console.log('cam apply err', e);
    }
    // 关键: 激活鼠标交互 (vtk.js style 需要 currentRenderer) + 相机变化时自动重绘
    try {
      var rw = getRW();
      var it = rw.getInteractor();
      it.setCurrentRenderer(rw.getRenderers()[0]);
      var cvs = document.querySelector('#vtk-root canvas');
      it.setContainer(cvs);
      it.bindEvents(cvs);
      it.setEnabled(true);
      // 相机变化 -> 强制重绘 (离线 viewer 默认不重绘)
      var cam = it.getCurrentRenderer ? it.getCurrentRenderer().getActiveCamera()
                                      : getCam();
      if (cam && cam.onModified && !window.__jb_camHooked) {
        window.__jb_camHooked = true;
        cam.onModified(function() { rw.render(); });
      }
      if (rw.render) rw.render();
    } catch (e) {
      console.log('interactor err', e);
    }
  }

  /* ---- 相机矩阵投影 (vtk: world -> view -> NDC -> screen) ---- */
  function matMul(a, b) { // 4x4 列主序相乘
    var r = new Array(16);
    for (var c = 0; c < 4; c++) for (var rw_ = 0; rw_ < 4; rw_++) {
      var s = 0;
      for (var k = 0; k < 4; k++) s += a[k*4+rw_] * b[c*4+k];
      r[c*4+rw_] = s;
    }
    return r;
  }
  function projVec(m, x, y, z, w) {
    var v = [
      m[0]*x + m[4]*y + m[8]*z  + m[12]*w,
      m[1]*x + m[5]*y + m[9]*z  + m[13]*w,
      m[2]*x + m[6]*y + m[10]*z + m[14]*w,
      m[3]*x + m[7]*y + m[11]*z + m[15]*w
    ];
    return v;
  }
  function worldToScreen(x, y, z, w, h) {
    var cam = getCam();
    if (!cam) return {x: w/2, y: h/2};
    // 相机参数 (标准 OpenGL 透视, 不依赖 vtk.js 矩阵内部布局)
    var pos = cam.getPosition();
    var foc = cam.getFocalPoint();
    var up = cam.getViewUp();
    var vangle = cam.getViewAngle();      // 垂直 FOV (度)
    var clip = cam.getClippingRange();
    // 相机基
    var vx0=foc[0]-pos[0], vy0=foc[1]-pos[1], vz0=foc[2]-pos[2];
    var vl=Math.sqrt(vx0*vx0+vy0*vy0+vz0*vz0); vx0/=vl; vy0/=vl; vz0/=vl;
    // right = normalize(cross(v, up))
    var rx=vy0*up[2]-vz0*up[1], ry=vz0*up[0]-vx0*up[2], rz=vx0*up[1]-vy0*up[0];
    var rl=Math.sqrt(rx*rx+ry*ry+rz*rz)||1; rx/=rl; ry/=rl; rz/=rl;
    // t = cross(right, v)
    var tx=ry*vz0-rz*vy0, ty=rz*vx0-rx*vz0, tz=rx*vy0-ry*vx0;
    var dx=x-pos[0], dy=y-pos[1], dz=z-pos[2];
    var cx=dx*rx+dy*ry+dz*rz;      // right
    var cy=dx*tx+dy*ty+dz*tz;      // up
    var cz=dx*vx0+dy*vy0+dz*vz0;   // depth (forward +)
    if (cz <= 0.1) cz = 0.1;
    var fov = vangle * Math.PI / 180;
    var tanF = Math.tan(fov/2);
    var ndcX = (cx/cz) / tanF / (w/h);   // 校正 aspect
    var ndcY = (cy/cz) / tanF;
    return {x: (ndcX+1)/2*w, y: (1-ndcY)/2*h, depth: cz};
  }

  function updateDomLabels() {
    if (!DOM_LABELS.length) return;
    var w = window.innerWidth, h = window.innerHeight;
    var placed = [];
    DOM_LABELS.forEach(function(l) {
      var p = worldToScreen(l.wx, l.wy, l.wz, w, h);
      var lx = p.x, ly = p.y;
      var ew = l.el.offsetWidth || 40, eh = l.el.offsetHeight || 16;
      var tries = 0;
      while (placed.some(function(r) {
        return Math.abs(lx - r.x) < (ew + r.w)/2 + 4 &&
               Math.abs(ly - r.y) < (eh + r.h)/2 + 3;
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
    SUBREGIONS.forEach(function(sr) {
      var el = document.createElement('div');
      el.className = 'jb-label';
      el.textContent = sr[3];
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
    ["mouseup", "touchend", "wheel", "mousemove", "keyup"].forEach(
      function(ev) { window.addEventListener(ev, function() { updateDomLabels(); }, true); });
    if (!window.__jb_legend_added) {
      window.__jb_legend_added = true;
      add_legend_panel();
    }
  }

  /* ---- 图例面板 ---- */
  function add_legend_panel() {
    var leg = document.createElement('div');
    leg.id = 'jb-legend';
    leg.style.cssText =
      'position:fixed;bottom:12px;right:12px;z-index:9997;' +
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
    document.getElementById('jb-leg-toggle').onclick = function() {
      if (leg.dataset.collapsed) {
        leg.parentNode.removeChild(leg);
        add_legend_panel();
      } else {
        leg.innerHTML = '<div style="font-weight:700;color:#333">' +
          'Yeo-7 Networks <span id="jb-leg-toggle" style="cursor:pointer;' +
          'color:#888;font-size:11px">[+]</span></div>';
        leg.dataset.collapsed = '1';
        document.getElementById('jb-leg-toggle').onclick = function() {
          leg.parentNode.removeChild(leg);
          add_legend_panel();
        };
      }
    };
  }

  /* ---- 截图: 走 renderWindow.captureImages (真实渲染) ---- */
  function dataURLtoBlob(du) {
    var bin = atob(du.split(',')[1]);
    var arr = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return new Blob([arr], {type: 'image/png'});
  }
  function dataURLtoImage(du) {
    return new Promise(function(res, rej) {
      var im = new Image();
      im.onload = function() { res(im); };
      im.onerror = rej;
      im.src = du;
    });
  }
  async function captureDataURL() {
    var rw = getRW();
    if (!rw || typeof rw.captureImages !== 'function') return null;
    var imgs = await rw.captureImages('image/png', {});
    var v = imgs && imgs[0];
    if (v && typeof v.then === 'function') v = await v;
    if (typeof v === 'string') return v;             // dataURL
    if (v instanceof Blob) {
      return new Promise(function(res) {
        var fr = new FileReader();
        fr.onload = function() { res(fr.result); };
        fr.readAsDataURL(v);
      });
    }
    return null;
  }

  /* ---- 带标签的合成截图: 底图 + DOM 标签 (烘焙) ---- */
  async function captureWithLabels() {
    var d = await captureDataURL();
    if (!d) return null;
    var img = await dataURLtoImage(d);
    var c = document.createElement('canvas');
    c.width = img.naturalWidth; c.height = img.naturalHeight;
    var ctx = c.getContext('2d');
    ctx.drawImage(img, 0, 0);
    // 画 DOM 标签 (按当前屏幕位置缩放)
    var scaleX = c.width / window.innerWidth;
    var scaleY = c.height / window.innerHeight;
    DOM_LABELS.forEach(function(l) {
      var el = l.el;
      var lx = parseFloat(el.style.left) * scaleX;
      var ly = parseFloat(el.style.top) * scaleY;
      var txt = el.textContent;
      ctx.font = '700 14px Arial, sans-serif';
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#FFFFFF';
      ctx.fillStyle = '#000000';
      ctx.lineJoin = 'round';
      ctx.strokeText(txt, lx, ly);
      ctx.fillText(txt, lx, ly);
    });
    return c;
  }
  async function captureWithLabelsURL(mime, q) {
    var c = await captureWithLabels();
    if (!c) return null;
    return c.toDataURL(mime, q);
  }

  function download(blob, name) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    setTimeout(function() { URL.revokeObjectURL(a.href); }, 1000);
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
      '&nbsp;|&nbsp;<label>旋转: <input type="range" id="jb-azim" ' +
      'min="0" max="360" step="5" value="45" style="width:120px">deg</label>' +
      '&nbsp;<span id="jb-hint" style="color:#888"></span>';
    document.body.appendChild(bar);
    var hint = document.getElementById('jb-hint');

    // 旋转控件: 直接操作相机 (不依赖交互器), 标签随相机投影自动跟随
    var BASE_POS = (window.JB_CAM && window.JB_CAM.pos) || [280, -280, 240];
    var BASE_FOC = (window.JB_CAM && window.JB_CAM.focal) || [0, 0, 5];
    var azim = document.getElementById('jb-azim');
    azim.addEventListener('input', function() {
      var deg = parseFloat(azim.value || '45');
      applyCameraAzimuth(deg);
    });
    function applyCameraAzimuth(deg) {
      var cam = getCam();
      if (!cam) return;
      var rad = deg * Math.PI / 180;
      var dx = BASE_POS[0] - BASE_FOC[0];
      var dy = BASE_POS[1] - BASE_FOC[1];
      var dz = BASE_POS[2] - BASE_FOC[2];
      var r = Math.sqrt(dx*dx + dy*dy);
      var baseAng = Math.atan2(dy, dx);
      var nx = BASE_FOC[0] + r * Math.cos(baseAng + rad);
      var ny = BASE_FOC[1] + r * Math.sin(baseAng + rad);
      var nz = BASE_FOC[2] + dz;
      cam.setPosition(nx, ny, nz);
      cam.setFocalPoint(BASE_FOC[0], BASE_FOC[1], BASE_FOC[2]);
      cam.setViewUp(0, 0, 1);
      cam.modified();
      var rw = getRW();
      if (rw && rw.render) rw.render();
      updateDomLabels();
      hint.textContent = deg + '°';
    }

    // PNG: 合成图 (底图+标签) 直接输出
    document.getElementById('jb-png').onclick = async function() {
      var d = await captureWithLabelsURL('image/png');
      if (!d) { hint.textContent = '截图失败'; return; }
      download(dataURLtoBlob(d), 'insula_view.png');
      hint.textContent = 'PNG 已导出';
    };
    // PDF: JPEG dataURL -> 内嵌最小 PDF (字节级编码, 避免 UTF-8 破坏二进制)
    document.getElementById('jb-pdf').onclick = async function() {
      var jpeg = await captureWithLabelsURL('image/jpeg', 0.95);
      if (!jpeg) { hint.textContent = '截图失败'; return; }
      var bin = atob(jpeg.split(',')[1]);
      var len = bin.length;
      var w = window.innerWidth, h = window.innerHeight;
      // 构建 PDF 各段对象的字节数组
      var parts = [];
      var headers = [
        '%PDF-1.4\n',
        '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
        '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
        '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + w + ' ' + h +
          '] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>\nendobj\n',
        '4 0 obj\n<< /Type /XObject /Subtype /Image /Width ' + w + ' /Height ' +
          h + ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode ' +
          '/Length ' + len + ' >>\nstream\n'
      ];
      parts.push(headers[0]);
      parts.push(headers[1]);
      parts.push(headers[2]);
      parts.push(headers[3]);
      parts.push(headers[4]);
      parts.push(bin);                       // JPEG 数据 (latin1 bytes)
      parts.push('\nendstream\nendobj\n');
      var stream = 'q ' + w + ' 0 0 ' + h + ' 0 0 cm /Im0 Do Q';
      parts.push('5 0 obj\n<< /Length ' + stream.length + ' >>\nstream\n' +
                 stream + '\nendstream\nendobj\n');
      // 计算 offsets (字节级)
      var pdfBytes = new Uint8Array(parts.reduce(function(a, p) {
        // 每个字符串按 latin1 逐字节
        return a + (typeof p === 'string' ? p.length : p.length);
      }, 0) + 512);
      var off = 0;
      var offsets = [];
      function writeStr(s) {
        for (var i = 0; i < s.length; i++) pdfBytes[off++] = s.charCodeAt(i) & 0xff;
      }
      // 重新组装 (track offsets for xref)
      var header2 = '%PDF-1.4\n';
      writeStr(header2);
      offsets.push(off);
      writeStr(headers[1]);      // obj1
      offsets.push(off);
      writeStr(headers[2]);      // obj2
      offsets.push(off);
      writeStr(headers[3]);      // obj3
      offsets.push(off);
      writeStr(headers[4]);      // obj4 header
      // JPEG bytes (latin1)
      for (var i = 0; i < bin.length; i++) pdfBytes[off++] = bin.charCodeAt(i) & 0xff;
      writeStr('\nendstream\nendobj\n');
      offsets.push(off);
      writeStr(parts[7]);        // obj5
      var xrefPos = off;
      var xref = 'xref\n0 6\n0000000000 65535 f \n';
      offsets.forEach(function(o) {
        xref += ('0000000000'+o).slice(-10) + ' 00000 n \n';
      });
      xref += 'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + xrefPos + '\n%%EOF';
      writeStr(xref);
      // 裁剪
      var out = pdfBytes.slice(0, off);
      download(new Blob([out], {type:'application/pdf'}), 'insula_view.pdf');
      hint.textContent = 'PDF 已导出';
    };
    // TIF: 合成图 -> RGB -> 最小 TIFF
    document.getElementById('jb-tif').onclick = async function() {
      var c = await captureWithLabels();
      if (!c) { hint.textContent = '截图失败'; return; }
      var w = c.width, h = c.height;
      var ctx = c.getContext('2d');
      var px = ctx.getImageData(0, 0, w, h).data;
      var rowBytes = w * 3, stripLen = rowBytes * h;
      var data = new Uint8Array(8 + 2 + 14*12 + 4 + stripLen);
      var dv = new DataView(data.buffer);
      data[0]=0x49; data[1]=0x49; data[2]=42; data[3]=0;
      dv.setUint32(4, 8, true);
      var ifd = 8;
      dv.setUint16(ifd, 14, true);
      var e = ifd + 2;
      var dataStart = ifd + 2 + 14*12 + 4;
      function E(tag, type, count, value) {
        dv.setUint16(e, tag, true); dv.setUint16(e+2, type, true);
        dv.setUint32(e+4, count, true);
        if (type === 3 && count === 1) { dv.setUint16(e+8, value, true); dv.setUint16(e+10, 0, true); }
        else { dv.setUint32(e+8, value, true); }
        e += 12;
      }
      E(256,4,1,w); E(257,4,1,h); E(258,3,1,8); E(259,3,1,1);
      E(262,3,1,2); E(273,4,1,dataStart); E(277,3,1,3); E(278,4,1,h);
      E(279,4,1,stripLen); E(282,3,1,72); E(283,3,1,72); E(284,3,1,1);
      E(296,3,1,2); E(305,2,1,0);
      dv.setUint32(ifd + 2 + 14*12, 0, true);
      for (var i = 0; i < h; i++) for (var x = 0; x < w; x++) {
        var s = (i*w+x)*4, d = dataStart + i*rowBytes + x*3;
        data[d]=px[s]; data[d+1]=px[s+1]; data[d+2]=px[s+2];
      }
      download(new Blob([data], {type:'image/tiff'}), 'insula_view.tif');
      hint.textContent = 'TIF 已导出';
    };

    function pngDataURLtoJpeg(du, q) {
      return dataURLtoImage(du).then(function(im) {
        var c = document.createElement('canvas');
        c.width = im.naturalWidth; c.height = im.naturalHeight;
        c.getContext('2d').drawImage(im, 0, 0);
        return c.toDataURL('image/jpeg', q);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addToolbar);
  } else {
    addToolbar();
  }
  waitOnView(subInjected);
  function waitOnView(cb, tries) {
    tries = tries || 0;
    var rw = getRW();
    if (rw) {
      applyInitCam();          // 应用 pyvista 相机 (iso/front/top)
      if (DOM_LABELS.length === 0) { cb(); return; }
    }
    if (tries > 400) return;
    setTimeout(function() { waitOnView(cb, tries + 1); }, 250);
  }
})();
</script>
"""


def inject_toolbar(html_path, out_path=None, subregions=None):
    html = open(html_path, 'r', encoding='utf-8').read()
    js_data = 'window.JB_SUBREGIONS = [];'
    if subregions:
        items = []
        for sr in subregions:
            x, y, z, lbl, color, text = sr
            items.append('[%s,%s,%s,"%s","%s","%s"]' % (x, y, z, lbl, color, text))
        js_data = 'window.JB_SUBREGIONS = [' + ','.join(items) + '];'
    inject = '<script>' + js_data + '</script>\n' + INJECT_JS
    html = html.replace('</body>', inject + '\n</body>')
    out = out_path or html_path
    # 注入相机初始参数 (iso 默认; 与 visualize_subregions de iso 一致)
    cam_js = ('window.JB_CAM = {pos:[280,-280,240], focal:[0,0,5], up:[0,0,1], clip:[0.01,2000]};')
    html = html.replace('<script>window.JB_SUBREGIONS',
                        '<script>' + cam_js + '</script>\n<script>window.JB_SUBREGIONS')
    open(out, 'w', encoding='utf-8').write(html)
    print('injected ->', out)
    return out


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(__file__), '..', '..', 'images', 'insula_viewer.html')
    dst = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(src), 'insula_viewer_exports.html')
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
            subregions.append((float(c[0]), float(c[1]), float(c[2]), lbl, shape, text))
        print(f'label data: {len(subregions)} subregions')
    except Exception as e:
        print('spec load failed:', e)
    inject_toolbar(src, dst, subregions)
