# -*- coding: utf-8 -*-
"""jellybrain.cli: 命令行入口.

用法:
  jellybrain --atlas brainnetome --region insula -o out.png
  jellybrain --atlas brainnetome --view front -o front.png
  jellybrain --interactive
"""
from __future__ import annotations

import argparse


def main(argv=None):
    p = argparse.ArgumentParser(prog='jellybrain',
                                description='玻璃脑果冻风格脑区亚区可视化')
    p.add_argument('--atlas', default='brainnetome',
                   help='图谱名 (默认 brainnetome)')
    p.add_argument('--region', default='insula',
                   help='脑区名 (默认 insula)')
    p.add_argument('--view', default='iso', choices=['iso', 'front', 'top'],
                   help='视角')
    p.add_argument('-o', '--output', default=None,
                   help='输出 PNG 路径; 缺省自动命名')
    p.add_argument('--no-labels', action='store_true',
                   help='关闭亚区标签')
    p.add_argument('--no-legend', action='store_true',
                   help='关闭图例')
    p.add_argument('--interactive', action='store_true',
                   help='打开 Jupyter 交互窗口 (trame)')
    p.add_argument('--html', default=None,
                   help='导出交互 HTML 路径')
    args = p.parse_args(argv)

    from . import atlases
    from .core import visualize_subregions

    spec = atlases.get_spec(args.atlas, args.region)
    output = args.output or f'{args.atlas}_{args.region}_{args.view}.png'

    if args.interactive or args.html:
        pl = visualize_subregions(
            spec, view=args.view, add_labels=not args.no_labels,
            show_legend=not args.no_legend, return_plotter=True)
        if args.html:
            pl.export_html(args.html)
            print(f'HTML -> {args.html}')
        if args.interactive:
            # 阻塞: 打开 trame 窗口 (于 Jupyter 或本地)
            pl.show(jupyter_backend='trame')
        return 0

    ok = visualize_subregions(
        spec, output=output, view=args.view,
        add_labels=not args.no_labels, show_legend=not args.no_legend)
    print(f'OK -> {output}')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
