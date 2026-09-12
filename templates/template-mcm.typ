// MCM/ICM 美赛 Typst 模板
// Based on COMAP MCM/ICM requirements

#let template(
  title: "Problem X: Title Here",
  team-number: "XXXXX",
  summary: none,
  body,
) = {
  // Page setup
  set page(
    paper: "us-letter",
    margin: (top: 1in, bottom: 1in, left: 1in, right: 1in),
    header: context {
      let page-num = counter(page).display("1")
      if page-num == "1" [] else {
        align(center)[#text(size: 9pt)[Team #team-number | Page #page-num]]
      }
    },
  )

  // Font settings
  set text(
    font: ("Times New Roman", "SimSun"),
    size: 12pt,
    lang: "en",
  )

  // Title
  align(center)[
    #text(size: 16pt, weight: "bold")[#title]
    #v(0.3em)
    #text(size: 11pt)[Team Control Number: #team-number]
  ]

  v(1em)

  // Summary sheet
  heading(level: 1)[Summary Sheet]
  if summary != none {
    summary
  } else {
    text(fill: gray)[Type your summary here...]
  }

  pagebreak()

  // Table of contents
  outline(title: "Table of Contents", indent: 1em)

  pagebreak()

  // Main body
  set heading(numbering: "1.1")

  // Heading styles
  show heading.where(level: 1): it => {
    v(1em)
    align(center)[#text(size: 14pt, weight: "bold")[#it]]
    v(0.5em)
  }

  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 13pt, weight: "bold")[#it]
    v(0.4em)
  }

  body

  // References
  pagebreak()
  heading(level: 1)[References]
  bibliography("refs.bib", style: "ieee")

  // Appendices
  pagebreak()
  heading(level: 1)[Appendices]
}

// Table with professional styling
#let pro-table(columns: (), align: auto, header: (), ..rows) = {
  let rows = rows.pos()
  table(
    columns: columns,
    align: align,
    stroke: (x, y) => {
      if y == 0 { (top: 1.5pt, bottom: 0.75pt) }
      else if y == rows.len() { (bottom: 1.5pt) }
      else { (bottom: 0.25pt) }
    },
    table.header(..header.map(h => text(weight: "bold")[#h])),
    ..rows.flatten(),
  )
}

// Equation with numbering
#let eq(label: none, body) = {
  math.equation(block: true, numbering: "(1)", label: label)[#body]
}

// Figure wrapper
#let fig(caption: none, label: none, body) = {
  figure(
    body,
    caption: caption,
    supplement: "Figure",
  ) #label
}
