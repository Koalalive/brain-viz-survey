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
/* ================= jellybrain 导出工具栏 ================= */
(function() {
  function waitForViewer(cb, tries) {
    tries = tries || 0;
    // trame offline viewer 挂载后, 全局 OfflineLocalView 已绑定到 #vtk-root
    var root = document.getElementById('vtk-root');
    // canvas 是 vtk 渲染目标
    var canv = document.querySelector('#vtk-root canvas, canvas');
    if (canv) { cb(canv); return; }
    if (tries > 100) return;
    setTimeout(function() { waitForViewer(cb, tries + 1); }, 200);
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
      // 强制同步渲染 (WebGL 读回需要 preserveDrawingBuffer; trame 通常已开)
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
    // PDF: 加载 jsPDF 后转换
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
    // TIF: canvas.toDataURL(png) -> tiff-js 编码
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
})();
</script>
"""


def inject_toolbar(html_path: str, out_path: str = None):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('</body>', INJECT_JS + '\n</body>')
    out = out_path or html_path
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('injected ->', out)
    return out


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(IMG := os.path.join(
            os.path.dirname(__file__), '..', '..', 'images'),
            'insula_viewer.html')
    dst = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(src), 'insula_viewer_exports.html')
    inject_toolbar(src, dst)
