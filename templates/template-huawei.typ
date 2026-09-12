// 华为杯研究生数学建模竞赛 Typst 模板
// 基于 2025 华为杯规范

#let template(
  title: "论文标题",
  school: "学校名称",
  team: "队伍编号",
  members: ("队员1", "队员2", "队员3"),
  advisor: "指导教师",
  abstract: none,
  keywords: (),
  body,
) = {
  // 页面设置
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2.8cm, right: 2.8cm),
    header: align(center)[#text(size: 9pt, fill: gray)[华为杯研究生数学建模竞赛]],
    footer: context {
      let page-num = counter(page).display("1")
      align(center)[#text(size: 9pt)[#page-num]]
    },
  )

  // 字体设置
  set text(
    font: ("SimSun", "Times New Roman"),
    size: 12pt,
    lang: "zh",
  )

  // 封面页
  align(center)[
    #text(size: 24pt, weight: "bold")[华为杯研究生数学建模竞赛]
    #v(2em)
    #text(size: 20pt, weight: "bold")[#title]
    #v(2em)
    #text(size: 14pt)[学校：#school]
    #v(0.5em)
    #text(size: 14pt)[队伍编号：#team]
    #v(0.5em)
    #text(size: 14pt)[队员：#members.join("、")]
    #v(0.5em)
    #text(size: 14pt)[指导教师：#advisor]
  ]

  pagebreak()

  // AI工具使用声明（2026新规）
  heading(level: 1)[AI工具使用声明]
  text(size: 10pt)[
    本文在研究和写作过程中使用了AI工具，声明如下：
    + 使用工具：Claude Code (Claude Fable 5)
    + 使用目的：辅助算法实现、论文排版、语法检查
    + 提示方式：自然语言对话
    + 内容采纳：经人工审核、修改后采纳，核心创新点均为作者原创
  ]

  // 摘要
  heading(level: 1)[摘要]
  if abstract != none {
    abstract
  } else {
    text(fill: gray)[在此输入摘要内容...]
  }

  if keywords.len() > 0 {
    v(0.5em)
    text(weight: "bold")[关键词：]
    text[#keywords.join("；")]
  }

  pagebreak()

  // 目录
  outline(title: "目录", indent: 1em)

  pagebreak()

  // 正文
  set heading(numbering: "1.1")

  // 一级标题居中
  show heading.where(level: 1): it => {
    align(center)[#it]
  }

  body

  // 参考文献
  pagebreak()
  heading(level: 1)[参考文献]
  bibliography("refs.bib", style: "gb-7714-2015")

  // 附录
  pagebreak()
  heading(level: 1)[附录]
  text(fill: gray)[在此添加附录内容（代码、数据等）...]
}

// 三线表
#let three-line-table(columns: (), align: auto, ..rows) = {
  let rows = rows.pos()
  table(
    columns: columns,
    align: align,
    stroke: none,
    table.hline(stroke: 1.5pt),
    table.header(..rows.first()),
    table.hline(stroke: 0.75pt),
    ..rows.slice(1).flatten(),
    table.hline(stroke: 1.5pt),
  )
}

// 公式
#let equation(label: none, body) = {
  math.equation(block: true, numbering: "(1)", label: label)[#body]
}

// 图表
#let figure-env(caption: none, label: none, body) = {
  figure(
    body,
    caption: caption,
    kind: "figure",
    supplement: "图",
  ) #label
}
