"""
图表清单生成 — 扫描 figures 目录,生成 figure_manifest.json
供论文自动嵌入图表使用。

用法:
    python scripts/gen_figure_manifest.py figures state/figure_manifest.json
"""

import argparse
import json
from pathlib import Path


def gen_manifest(figures_dir, output_path):
    """扫描 figures 目录,生成图表清单"""
    manifest = []
    png_dir = Path(figures_dir) / "png"
    pdf_dir = Path(figures_dir) / "pdf"

    if not png_dir.exists():
        print(f"[WARN] PNG 目录不存在: {png_dir}")
        return manifest

    for png_file in sorted(png_dir.glob("*.png")):
        pdf_file = pdf_dir / (png_file.stem + ".pdf")
        manifest.append({
            "id": png_file.stem,           # fig1_xxx
            "png_path": png_file.as_posix(),     # figures/png/fig1_xxx.png
            "pdf_path": pdf_file.as_posix() if pdf_file.exists() else None,
            "caption": "",                 # 待填写:图1 [对象][趋势]([关键数值])
            "chapter": "",                 # 待填写:5.1 / 5.2 / ...
            "latex_ref": "",               # 自动生成:\includegraphics{...}
            "typst_ref": ""                # 自动生成:image(...)
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] figure_manifest.json 已生成: {output_path} ({len(manifest)} 张图表)")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图表清单生成 — 扫描 figures 生成 figure_manifest.json")
    parser.add_argument("figures_dir", nargs="?", default="figures", help="figures 目录")
    parser.add_argument("output_path", nargs="?", default="state/figure_manifest.json", help="输出路径")
    args = parser.parse_args()
    gen_manifest(args.figures_dir, args.output_path)
