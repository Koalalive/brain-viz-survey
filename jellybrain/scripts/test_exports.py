# -*- coding: utf-8 -*-
"""完整验收测试: 导出 PNG/PDF/TIF 非空白 + 标签跟随旋转.

对 insula_viewer_exports.html 用 playwright:
  - 点击导出, 下载文件, 用 PIL/字节校验非空白
  - 拖拽旋转, 记录标签屏幕位置变化 (跟随检验).
"""
import os
import sys
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

        # 1. 标签渲染数量
        results['labels'] = page.evaluate(
            'document.querySelectorAll(".jb-label").length')

        # 2. 标签位置 (旋转前)
        pos_before = page.evaluate('''() => {
          return Array.from(document.querySelectorAll(".jb-label"))
            .map(e => [Math.round(e.offsetLeft), Math.round(e.offsetTop)]);
        }''')

        # 3. 旋转 (用滑块控件, 可靠) -> 标签跟随
        page.fill('#jb-azim', '135')
        page.dispatch_event('#jb-azim', 'input')
        page.wait_for_timeout(1200)
        pos_after = page.evaluate('''() => {
          return Array.from(document.querySelectorAll(".jb-label"))
            .map(e => [Math.round(e.offsetLeft), Math.round(e.offsetTop)]);
        }''')
        moved = sum(1 for a, c in zip(pos_before, pos_after)
                    if abs(a[0] - c[0]) + abs(a[1] - c[1]) > 5)
        results['labels_moved_after_rotate'] = f'{moved}/{len(pos_before)}'

        # 4. 导出三格式并下载
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

    # 5. 校验文件内容
    from PIL import Image
    import numpy as np
    png = os.path.join(OUT, 'v.png')
    if os.path.exists(png):
        im = np.array(Image.open(png).convert('L'))
        nonwhite = (im < 240).sum()
        print(f'PNG content: nonwhite pixels = {nonwhite} '
              f'({"HAS CONTENT" if nonwhite > 10000 else "BLANK!"})')
    pdf = os.path.join(OUT, 'v.pdf')
    if os.path.exists(pdf):
        head = open(pdf, 'rb').read(8)
        print('PDF header:', head[:8])
        print('PDF size:', os.path.getsize(pdf))
    tif = os.path.join(OUT, 'v.tif')
    if os.path.exists(tif):
        try:
            im = Image.open(tif)
            arr = np.array(im.convert('L'))
            print(f'TIF PIL ok: {im.format} {im.size}, nonwhite={((arr<240).sum())}')
        except Exception as e:
            print('TIF open err:', e)


if __name__ == '__main__':
    main()
