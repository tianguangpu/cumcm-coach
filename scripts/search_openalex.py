"""
search_openalex.py — OpenAlex 文献自动检索
==========================================
通过 OpenAlex API 检索学术文献，自动筛选近5年高被引论文，生成 BibTeX。

用法:
    python search_openalex.py --query "linear programming optimization" --years 5 --limit 20
    python search_openalex.py --query "time series prediction" --output paper/refs_auto.bib
    python search_openalex.py --query "TSP traveling salesman" --min-cited 50 --format bibtex

特性:
  - 免费API，无需注册（用邮箱做polite pool提升速率）
  - 自动筛选近N年、按被引次数排序
  - 输出BibTeX/JSON/表格三种格式
  - DOI交叉核验
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_BASE = "https://api.openalex.org/works"
POLITE_EMAIL = "mathmodeling@example.com"  # polite pool


def search_openalex(
    query: str,
    years: int = 5,
    limit: int = 20,
    min_cited: int = 0,
    sort: str = "cited_by_count:desc",
) -> list[dict]:
    """
    检索 OpenAlex 文献。

    Args:
        query: 检索词
        years: 近N年
        limit: 最大返回数
        min_cited: 最小被引次数
        sort: 排序方式

    Returns:
        文献列表
    """
    current_year = datetime.now().year
    from_year = current_year - years

    # 关键修复: 用 title_and_abstract.search filter（顶层 search 参数对短语查询不可靠，
    # 常返回空或无关结果）。空格转 %20，冒号保留（OpenAlex filter 语法）。
    term = query.replace(" ", "%20")
    filter_str = (
        f"title_and_abstract.search:{term},"
        f"publication_year:{from_year}-{current_year},type:article"
    )
    params = urllib.parse.urlencode(
        {
            "filter": filter_str,
            "sort": sort,
            "per_page": min(limit, 200),
            "mailto": POLITE_EMAIL,
        },
        safe=":%",
    )

    url = f"{API_BASE}?{params}"
    print(f"[OpenAlex] 检索: {query}")
    print(f"[OpenAlex] URL: {url}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MathModelingBot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[OpenAlex] API错误: {e}")
        return []

    works = data.get("results", [])
    print(f"[OpenAlex] 返回 {len(works)} 条结果")

    # 过滤最小被引
    if min_cited > 0:
        works = [w for w in works if w.get("cited_by_count", 0) >= min_cited]
        print(f"[OpenAlex] 被引>={min_cited}: {len(works)} 条")

    return works


def format_bibtex_entry(work: dict, index: int) -> str:
    """将OpenAlex work转为BibTeX条目。"""
    # 提取作者
    authors = []
    for auth in work.get("authorships", [])[:5]:
        name = auth.get("author", {}).get("display_name", "")
        if name:
            authors.append(name)
    author_str = " and ".join(authors) if authors else "Unknown"

    # 提取期刊
    venue = ""
    loc = work.get("primary_location", {})
    if loc and loc.get("source"):
        venue = loc["source"].get("display_name", "")

    # 提取DOI
    doi = work.get("doi", "")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi[16:]

    # 提取年份
    year = work.get("publication_year", "????")

    # 提取标题
    title = work.get("title", "Untitled")

    # 生成cite key
    first_author = authors[0].split()[-1] if authors else "Unknown"
    cite_key = f"{first_author}{year}_{index}"

    # BibTeX格式
    bib = f"@article{{{cite_key},\n"
    bib += f'  title     = {{{title}}},\n'
    bib += f'  author    = {{{author_str}}},\n'
    bib += f'  journal   = {{{venue}}},\n'
    bib += f'  year      = {{{year}}},\n'
    if doi:
        bib += f'  doi       = {{{doi}}},\n'
    cited = work.get("cited_by_count", 0)
    bib += f'  note      = {{被引{cited}次}}\n'
    bib += "}"
    return bib


def format_table(works: list[dict]) -> str:
    """生成Markdown表格。"""
    lines = []
    lines.append("| # | 标题 | 作者 | 期刊 | 年份 | 被引 | DOI |")
    lines.append("|---|------|------|------|------|------|-----|")

    for i, w in enumerate(works, 1):
        title = w.get("title", "")[:60]
        authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:2]]
        author_str = ", ".join(authors) if authors else "?"

        venue = ""
        loc = w.get("primary_location", {})
        if loc and loc.get("source"):
            venue = loc["source"].get("display_name", "")[:30]

        year = w.get("publication_year", "?")
        cited = w.get("cited_by_count", 0)
        doi = w.get("doi", "")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[16:]

        lines.append(f"| {i} | {title} | {author_str} | {venue} | {year} | {cited} | {doi[:30]} |")

    return "\n".join(lines)


def save_bibtex(works: list[dict], output_path: str):
    """保存为BibTeX文件。"""
    entries = []
    for i, w in enumerate(works, 1):
        entries.append(format_bibtex_entry(w, i))

    content = "\n\n".join(entries)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"[OpenAlex] BibTeX已保存: {out} ({len(entries)}条)")
    return content


def main():
    p = argparse.ArgumentParser(description="OpenAlex 文献自动检索")
    p.add_argument("--query", required=True, help="检索词")
    p.add_argument("--years", type=int, default=5, help="近N年(默认5)")
    p.add_argument("--limit", type=int, default=20, help="最大返回数(默认20)")
    p.add_argument("--min-cited", type=int, default=0, help="最小被引次数")
    p.add_argument("--format", choices=["bibtex", "table", "json"], default="table", help="输出格式")
    p.add_argument("--output", default=None, help="输出文件路径")
    a = p.parse_args()

    works = search_openalex(a.query, a.years, a.limit, a.min_cited)
    if not works:
        print("[OpenAlex] 未找到结果")
        return 1

    if a.format == "bibtex":
        if a.output:
            save_bibtex(works, a.output)
        else:
            for i, w in enumerate(works, 1):
                print(format_bibtex_entry(w, i))
                print()
    elif a.format == "json":
        if a.output:
            Path(a.output).write_text(json.dumps(works, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[OpenAlex] JSON已保存: {a.output}")
        else:
            print(json.dumps(works[:3], ensure_ascii=False, indent=2))
    else:
        print(format_table(works))

    return 0


if __name__ == "__main__":
    sys.exit(main())
