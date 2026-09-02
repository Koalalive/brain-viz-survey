# -*- coding: utf-8 -*-
"""inject_toolbar: 无悬浮标签版本.

保留:
  - 原生鼠标旋转 (相机 onModified -> render)
  - 旋转滑块 (备用微调)
  - PNG / PDF / TIF 导出 (字节级 PDF, 内嵌 JPEG)
  - Yeo-7 图例面板 (右下角, 可折叠)
删除: 悬浮文字标签.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

INJECT_JS = r"""
<script>
/* ============ jellybrain viewer: 鼠标旋转 + 图例 + 导出 (无悬浮标签) ============ */
(function() {
  var CAM_INIT = window.JB_CAM || null;

  function getRW() {
    return (window.global && window.global.renderWindow)
      ? window.global.renderWindow : null;
  }
  // 主渲染器: 含 actors 的那个 (可能有空背景渲染器在前)
  function getMainRen() {
    var rw = getRW();
    if (!rw || !rw.getRenderers) return null;
    var rs = rw.getRenderers(), best = null, bestN = -1;
    for (var i = 0; i < rs.length; i++) {
      var n = 0;
      try { n = rs[i].getActors ? rs[i].getActors().length : 0; } catch (e) {}
      if (n > bestN) { bestN = n; best = rs[i]; }
    }
    return best || rs[0];
  }
  function getCam() {
    var ren = getMainRen();
    return ren ? ren.getActiveCamera() : null;
  }

  /* ---- 初始化: 相机 + 交互器 + 自动重绘 ---- */
  function initViewer() {
    var rw = getRW();
    if (!rw) return;
    var cam = getCam();
    if (CAM_INIT && cam) {
      try {
        cam.setPosition(CAM_INIT.pos[0], CAM_INIT.pos[1], CAM_INIT.pos[2]);
        cam.setFocalPoint(CAM_INIT.focal[0], CAM_INIT.focal[1],
                          CAM_INIT.focal[2]);
        cam.setViewUp(CAM_INIT.up[0], CAM_INIT.up[1], CAM_INIT.up[2]);
        cam.setClippingRange(CAM_INIT.clip[0], CAM_INIT.clip[1]);
      } catch (e) {}
    }
    try {
      var it = rw.getInteractor();
      var ren = getMainRen();
      it.setCurrentRenderer(ren);
      var cvs = document.querySelector('#vtk-root canvas');
      it.setContainer(cvs);
      it.bindEvents(cvs);
      it.setEnabled(true);
      // 交互事件 -> 强制重绘 (相机实例可能被重建, 用交互器事件更稳)
      if (it.onInteraction && !window.__jb_itHooked) {
        window.__jb_itHooked = true;
        it.onInteraction(function() { rw.render(); });
        if (it.onEndInteraction) {
          it.onEndInteraction(function() { rw.render(); });
        }
      }
      if (rw.render) rw.render();
    } catch (e) { console.log('init err', e); }
  }

  /* ---- Yeo-7 图例面板 ---- */
  function add_legend_panel() {
    if (document.getElementById('jb-legend')) return;
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
        add_legend_panel_remove(leg);
      } else {
        leg.innerHTML = '<div style="font-weight:700;color:#333">' +
          'Yeo-7 Networks <span id="jb-leg-toggle" style="cursor:pointer;' +
          'color:#888;font-size:11px">[+]</span></div>';
        leg.dataset.collapsed = '1';
        document.getElementById('jb-leg-toggle').onclick = function() {
          add_legend_panel_remove(leg);
        };
      }
    };
  }
  function add_legend_panel_remove(oldLeg) {
    if (oldLeg && oldLeg.parentNode) oldLeg.parentNode.removeChild(oldLeg);
    add_legend_panel();
  }

  /* ---- 截图 ---- */
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
    if (typeof v === 'string') return v;
    if (v instanceof Blob) {
      return new Promise(function(res) {
        var fr = new FileReader();
        fr.onload = function() { res(fr.result); };
        fr.readAsDataURL(v);
      });
    }
    return null;
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

    // 旋转滑块 (备用角度微调)
    var BASE_POS = (CAM_INIT && CAM_INIT.pos) || [280, -280, 240];
    var BASE_FOC = (CAM_INIT && CAM_INIT.focal) || [0, 0, 5];
    var azim = document.getElementById('jb-azim');
    azim.addEventListener('input', function() {
      applyAzimuth(parseFloat(azim.value || '45'));
    });
    function applyAzimuth(deg) {
      var cam = getCam();
      if (!cam) return;
      var rad = deg * Math.PI / 180;
      var dx = BASE_POS[0] - BASE_FOC[0], dy = BASE_POS[1] - BASE_FOC[1];
      var dz = BASE_POS[2] - BASE_FOC[2];
      var r = Math.sqrt(dx*dx + dy*dy);
      var baseAng = Math.atan2(dy, dx);
      cam.setPosition(BASE_FOC[0] + r*Math.cos(baseAng+rad),
                      BASE_FOC[1] + r*Math.sin(baseAng+rad),
                      BASE_FOC[2] + dz);
      cam.setFocalPoint(BASE_FOC[0], BASE_FOC[1], BASE_FOC[2]);
      cam.setViewUp(0, 0, 1);
      cam.modified();
      var rw = getRW();
      if (rw && rw.render) rw.render();
      hint.textContent = deg + '°';
    }

    // PNG
    document.getElementById('jb-png').onclick = async function() {
      var d = await captureDataURL();
      if (!d) { hint.textContent = '截图失败'; return; }
      download(dataURLtoBlob(d), 'insula_view.png');
      hint.textContent = 'PNG 已导出';
    };
    // PDF (字节级, JPEG 内嵌)
    document.getElementById('jb-pdf').onclick = async function() {
      var d = await captureDataURL();
      if (!d) { hint.textContent = '截图失败'; return; }
      var img = await dataURLtoImage(d);
      var c = document.createElement('canvas');
      c.width = img.naturalWidth; c.height = img.naturalHeight;
      c.getContext('2d').drawImage(img, 0, 0);
      var jpeg = c.toDataURL('image/jpeg', 0.95);
      var bin = atob(jpeg.split(',')[1]);
      var len = bin.length;
      var w = c.width, h = c.height;
      var objects = [
        '%PDF-1.4\n',
        '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
        '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
        '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + w + ' ' + h +
          '] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>\nendobj\n',
        '4 0 obj\n<< /Type /XObject /Subtype /Image /Width ' + w + ' /Height ' +
          h + ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode ' +
          '/Length ' + len + ' >>\nstream\n'
      ];
      var stream = 'q ' + w + ' 0 0 ' + h + ' 0 0 cm /Im0 Do Q';
      var obj5 = '5 0 obj\n<< /Length ' + stream.length + ' >>\nstream\n' +
                 stream + '\nendstream\nendobj\n';
      var endstream = '\nendstream\nendobj\n';
      var total = 0;
      objects.forEach(function(s) { total += s.length; });
      total += len + endstream.length + obj5.length;
      var buf = new Uint8Array(total + 512);
      var off = 0, offsets = [];
      function ws(s) {
        for (var i = 0; i < s.length; i++) buf[off++] = s.charCodeAt(i) & 0xff;
      }
      ws(objects[0]);                              // header
      offsets.push(off);
      ws(objects[1]);                              // obj1
      offsets.push(off);
      ws(objects[2]);                              // obj2
      offsets.push(off);
      ws(objects[3]);                              // obj3
      offsets.push(off);
      ws(objects[4]);                              // obj4 header
      for (var i = 0; i < bin.length; i++) {       // JPEG bytes (latin1)
        buf[off++] = bin.charCodeAt(i) & 0xff;
      }
      ws(endstream);
      offsets.push(off);
      ws(obj5);
      var xrefPos = off;
      var xref = 'xref\n0 6\n0000000000 65535 f \n';
      offsets.forEach(function(o) {
        xref += ('0000000000'+o).slice(-10) + ' 00000 n \n';
      });
      xref += 'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + xrefPos +
              '\n%%EOF';
      ws(xref);
      download(new Blob([buf.slice(0, off)], {type: 'application/pdf'}),
               'insula_view.pdf');
      hint.textContent = 'PDF 已导出';
    };
    // TIF (最小未压缩)
    document.getElementById('jb-tif').onclick = async function() {
      var d = await captureDataURL();
      if (!d) { hint.textContent = '截图失败'; return; }
      var img = await dataURLtoImage(d);
      var c = document.createElement('canvas');
      c.width = img.naturalWidth; c.height = img.naturalHeight;
      var ctx = c.getContext('2d');
      ctx.drawImage(img, 0, 0);
      var px = ctx.getImageData(0, 0, c.width, c.height).data;
      var w = c.width, h = c.height;
      var rowBytes = w*3, stripLen = rowBytes*h;
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
        if (type === 3 && count === 1) {
          dv.setUint16(e+8, value, true); dv.setUint16(e+10, 0, true);
        } else {
          dv.setUint32(e+8, value, true);
        }
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
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addToolbar);
  } else {
    addToolbar();
  }
  function waitView(cb, tries) {
    tries = tries || 0;
    if (getRW()) {
      initViewer();
      if (!window.__jb_legend_added) {
        window.__jb_legend_added = true;
        add_legend_panel();
      }
      cb();
      return;
    }
    if (tries > 400) return;
    setTimeout(function() { waitView(cb, tries + 1); }, 250);
  }
  waitView(function() {});
})();
</script>
"""


def inject_toolbar(html_path, out_path=None):
    html = open(html_path, 'r', encoding='utf-8').read()
    cam_js = ('<script>window.JB_CAM = {pos:[280,-280,240], focal:[0,0,5], '
              'up:[0,0,1], clip:[0.01,2000]};</script>')
    inject = cam_js + '\n' + INJECT_JS
    html = html.replace('</body>', inject + '\n</body>')
    out = out_path or html_path
    open(out, 'w', encoding='utf-8').write(html)
    print('injected ->', out)
    return out


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(__file__), '..', '..', 'images',
                     'insula_viewer.html')
    dst = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(src), 'insula_viewer_exports.html')
    inject_toolbar(src, dst)
