# -*- coding: utf-8 -*-
"""无标签版验收测试.

对 insula_viewer_exports.html 用 playwright:
  - 无悬浮文字标签 (.jb-label == 0)
  - Yeo-7 图例面板存在
  - 鼠标拖拽 -> 相机变化 + 场景重绘 (截图像素差异)
  - 导出 PNG/PDF/TIF 非空白
"""
import os
import json

from playwright.sync_api import sync_playwright

HTML = r'C:\Users\29698\brain-viz-survey\images\insula_viewer_exports.html'
OUT = r'C:\Users\29698\AppData\Local\Temp\opencode\final_test'
os.makedirs(OUT, exist_ok=True)


def main():
    results = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel='msedge')
        ctx = b.new_context(accept_downloads=True,
                            viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        page.goto('file:///' + HTML.replace('\\', '/'))
        page.wait_for_timeout(9500)

        # 1. 无悬浮标签 + 图例存在
        results['jb-label_count'] = page.evaluate(
            'document.querySelectorAll(".jb-label").length')
        results['legend_present'] = page.evaluate(
            '!!document.getElementById("jb-legend")')

        # 2. 相机位置 (拖拽前, 取含 actors 的主渲染器)
        cam_before = page.evaluate('''() => {
          var rw = window.global.renderWindow;
          var rs = rw.getRenderers(), best = null, n = -1;
          rs.forEach(function(r) {
            var c = 0;
            try { c = r.getActors().length; } catch (e) {}
            if (c > n) { n = c; best = r; }
          });
          return best.getActiveCamera().getPosition();
        }''')
        results['cam_before'] = [round(v, 1) for v in cam_before]

        # 3. 截图 (画面基准)
        shot0 = os.path.join(OUT, 'shot0.png')
        page.screenshot(path=shot0)

        # 4. 拖拽旋转
        page.mouse.move(400, 400)
        page.mouse.down()
        page.mouse.move(560, 300, steps=12)
        page.mouse.move(620, 280, steps=6)
        page.mouse.up()
        page.wait_for_timeout(1500)

        # 5. 相机变化 + 画面重绘
        cam_after = page.evaluate('''() => {
          var rw = window.global.renderWindow;
          var rs = rw.getRenderers(), best = null, n = -1;
          rs.forEach(function(r) {
            var c = 0;
            try { c = r.getActors().length; } catch (e) {}
            if (c > n) { n = c; best = r; }
          });
          return best.getActiveCamera().getPosition();
        }''')
        results['cam_after'] = [round(v, 1) for v in cam_after]
        dist = sum((a - c) ** 2 for a, c in zip(cam_before, cam_after)) ** 0.5
        results['camera_moved'] = round(dist, 1)

        shot1 = os.path.join(OUT, 'shot1.png')
        page.screenshot(path=shot1)

        # 6. 导出三格式
        for btn, name in [('jb-png', 'v.png'), ('jb-pdf', 'v.pdf'),
                          ('jb-tif', 'v.tif')]:
            try:
                with page.expect_download(timeout=60000) as dl:
                    page.click('#' + btn)
                d = dl.value
                path = os.path.join(OUT, name)
                d.save_as(path)
                results[btn] = f'{os.path.getsize(path)} bytes'
            except Exception as e:
                results[btn] = 'ERR ' + str(e)[:80]

        page.wait_for_timeout(1500)
        b.close()
    print(json.dumps(results, indent=2))

    # 7. 像素差异 (画面确实重绘)
    from PIL import Image
    import numpy as np
    a0 = np.array(Image.open(shot0).convert('L'))
    a1 = np.array(Image.open(shot1).convert('L'))
    diff = int((np.abs(a0.astype(int) - a1.astype(int)) > 20).sum())
    print(f'redraw diff pixels = {diff} '
          f'({"SCENE REPAINTED" if diff > 5000 else "CHECK!"})')

    # 8. 文件内容校验
    png = os.path.join(OUT, 'v.png')
    if os.path.exists(png):
        im = np.array(Image.open(png).convert('L'))
        nonwhite = (im < 240).sum()
        print(f'PNG content: nonwhite = {nonwhite} '
              f'({"HAS CONTENT" if nonwhite > 10000 else "BLANK!"})')
    pdf = os.path.join(OUT, 'v.pdf')
    if os.path.exists(pdf):
        data = open(pdf, 'rb').read()
        print('PDF header:', data[:8])
        print('PDF JPEG embedded:', data.find(b'\xff\xd8') >= 0,
              '| size:', len(data))
    tif = os.path.join(OUT, 'v.tif')
    if os.path.exists(tif):
        im = Image.open(tif)
        arr = np.array(im.convert('L'))
        print(f'TIF PIL ok: {im.format} {im.size}, '
              f'nonwhite={((arr < 240).sum())}')


if __name__ == '__main__':
    main()
