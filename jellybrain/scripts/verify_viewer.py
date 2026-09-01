# -*- coding: utf-8 -*-
"""用系统 Edge/Chrome 验证 trame viewer HTML 可加载 + 工具栏已注入."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

HTML = r'C:\Users\29698\brain-viz-survey\images\insula_viewer_exports.html'
SHOT = r'C:\Users\29698\brain-viz-survey\images\_viewer_check.png'

def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = None
        for channel in ('msedge', 'chrome'):
            try:
                browser = p.chromium.launch(channel=channel)
                print('launched with', channel)
                break
            except Exception as e:
                print('fail', channel, str(e)[:80])
        if browser is None:
            print('NO BROWSER AVAILABLE')
            return
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        page.goto('file:///' + HTML.replace('\\', '/'))
        page.wait_for_timeout(6000)  # 等 vtk 加载
        # 检查工具栏
        toolbar = page.locator('#jb-toolbar')
        has_toolbar = toolbar.count() > 0
        print('toolbar present:', has_toolbar)
        has_png = page.locator('#jb-png').count() > 0
        has_pdf = page.locator('#jb-pdf').count() > 0
        has_tif = page.locator('#jb-tif').count() > 0
        print('buttons png/pdf/tif:', has_png, has_pdf, has_tif)
        # 检查 canvas 渲染
        canv = page.locator('canvas')
        print('canvas count:', canv.count())
        if canv.count() > 0:
            page.screenshot(path=SHOT)
            print('screenshot saved:', SHOT)
        browser.close()


if __name__ == '__main__':
    main()
