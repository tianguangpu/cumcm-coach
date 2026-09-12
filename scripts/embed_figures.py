"""
图表自动嵌入 — 读取 figure_manifest.json,在对应章节文件中插入图表引用

用法:
    python scripts/embed_figures.py paper/sections state/figure_manifest.json latex
    python scripts/embed_figures.py paper/sections state/figure_manifest.json typst
"""

import argparse
import json
from pathlib import Path


def embed_figures(section_dir, manifest_path, engine="latex", prefix="../"):
    """读取 manifest,自动在对应章节文件中插入图表引用"""
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    embedded = 0
    for fig in manifest:
        if not fig["chapter"] or not fig["caption"]:
            print(f"[SKIP] {fig['id']}: 未配置 chapter 或 caption")
            continue

        # 找到对应章节文件
        chapter_num = fig["chapter"].split(".")[0]
        section_file = None
        for tex_file in Path(section_dir).glob("*"):
            if tex_file.stem.startswith(f"{chapter_num}_"):
                section_file = tex_file
                break

        if not section_file:
            print(f"[WARN] 未找到章节 {chapter_num} 的文件,跳过 {fig['id']}")
            continue

        # 统一路径分隔符为正斜杠（Windows 上 str(Path) 返回反斜杠，会破坏 LaTeX 的 \pdf 等命令）
        pdf_path = prefix + (fig["pdf_path"] or "").replace("\\", "/")

        # 生成引用代码
        if engine == "latex":
            ref_code = f"""
\\begin{{figure}}[H]
\\centering
\\includegraphics[width=0.85\\textwidth]{{{pdf_path}}}
\\caption{{{fig['caption']}}}
\\label{{fig:{fig['id']}}}
\\end{{figure}}
"""
        else:  # typst
            ref_code = f"""
#figure(
  image("{pdf_path}", width: 85%),
  caption: [{fig['caption']}]
) <fig_{fig['id']}>
在 @fig_{fig['id']} 中可以看到...
"""

        # 插入到章节文件末尾
        content = section_file.read_text(encoding="utf-8")
        if fig['id'] not in content:  # 避免重复插入
            content += f"\n% === 自动嵌入: {fig['id']} ===\n{ref_code}"
            section_file.write_text(content, encoding="utf-8")
            print(f"[OK] 已嵌入 {fig['id']} → {section_file.name}")
            embedded += 1
        else:
            print(f"[SKIP] {fig['id']}: 已存在于 {section_file.name}")

    print(f"[DONE] 共嵌入 {embedded} 张图表")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图表自动嵌入 — 读取 figure_manifest.json 插入图表引用")
    parser.add_argument("section_dir", nargs="?", default="paper/sections", help="章节目录")
    parser.add_argument("manifest_path", nargs="?", default="state/figure_manifest.json", help="图表清单路径")
    parser.add_argument("engine", nargs="?", default="latex", choices=["latex", "typst"], help="排版引擎")
    parser.add_argument("--prefix", default="../", help="图表相对路径前缀(相对 main.tex 所在目录;v7 项目结构 figures/ 在根、paper/ 在子目录时为 ../)")
    args = parser.parse_args()
    embed_figures(args.section_dir, args.manifest_path, args.engine, args.prefix)
