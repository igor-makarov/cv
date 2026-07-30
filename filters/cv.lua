local function stringify(block)
  return pandoc.utils.stringify(block)
end

local function unwrap_strong(para)
  if para and para.t == "Para" and #para.content == 1 and para.content[1].t == "Strong" then
    return para.content[1].content
  end
  return para and para.content or {}
end

local title_tracking = {
  {"Ig", "n24", "Title Track -24"},
  {"o", "n30", "Title Track -30"},
  {"r", "n20", "Title Track -20"},
  {" ", "none", nil},
  {"M", "n20", "Title Track -20"},
  {"a", "n8", "Title Track -8"},
  {"k", "p4", "Title Track +4"},
  {"a", "n20", "Title Track -20"},
  {"r", "n14", "Title Track -14"},
  {"ov", "n10", "Title Track -10"},
  {" ", "n10", "Title Track -10"},
}

local function tracked_title(format)
  local inlines = pandoc.Inlines({})
  for _, run in ipairs(title_tracking) do
    if run[2] == "none" then
      inlines:insert(pandoc.Space())
    else
      local content = run[1] == " " and {pandoc.Space()} or {pandoc.Str(run[1])}
      local attr
      if format == "html" then
        attr = pandoc.Attr("", {"title-track-" .. run[2]})
      else
        attr = pandoc.Attr("", {}, {{"custom-style", run[3]}})
      end
      inlines:insert(pandoc.Span(content, attr))
    end
  end
  return inlines
end

local function split_heading(inlines)
  for index, inline in ipairs(inlines) do
    if inline.t == "Str" and inline.text == "—" then
      local left = {}
      local right = {}
      for i = 1, index - 1 do
        table.insert(left, inlines[i])
      end
      for i = index + 1, #inlines do
        table.insert(right, inlines[i])
      end
      while left[#left] and left[#left].t == "Space" do
        table.remove(left)
      end
      while right[1] and right[1].t == "Space" do
        table.remove(right, 1)
      end
      return left, right
    end
  end
  error("Expected an em dash in level-three heading: " .. pandoc.utils.stringify(inlines))
end

local function structured_contact(inlines)
  local groups = {}
  local current = pandoc.Inlines({})

  local function finish_group()
    while current[1] and current[1].t == "Space" do
      table.remove(current, 1)
    end
    while current[#current] and current[#current].t == "Space" do
      table.remove(current)
    end
    if #current > 0 then
      table.insert(groups, current)
    end
    current = pandoc.Inlines({})
  end

  for _, inline in ipairs(inlines) do
    if inline.t == "Str" and inline.text == "·" then
      finish_group()
    else
      current:insert(inline)
    end
  end
  finish_group()

  local output = pandoc.Inlines({})
  for index, group in ipairs(groups) do
    output:insert(pandoc.Span(group, pandoc.Attr("", {"contact-item"})))
    if index < #groups then
      output:insert(pandoc.Space())
      output:insert(pandoc.Span({pandoc.Str("·")}, pandoc.Attr("", {"contact-separator"})))
      output:insert(pandoc.Space())
    end
  end
  return output
end

local function html_document(doc)
  local blocks = doc.blocks
  if #blocks < 3 or blocks[1].t ~= "Header" or blocks[1].level ~= 1 then
    error("cv.md must begin with a level-one name heading, role, and contact line")
  end

  local title = blocks[1]
  if stringify(title) ~= "Igor Makarov" then
    error("Expected the CV title to be Igor Makarov")
  end
  local role = unwrap_strong(blocks[2])
  local contact = pandoc.walk_block(blocks[3], {
    Link = function(link)
      link.attributes.target = "_blank"
      link.attributes.rel = "noopener noreferrer"
      return link
    end,
  })
  contact.content = structured_contact(contact.content)
  title.content = tracked_title("html")
  title.content:insert(pandoc.Span(role, pandoc.Attr("", {"role"})))
  local hero = pandoc.Div({title, pandoc.Div({contact}, pandoc.Attr("", {"contact"}))}, pandoc.Attr("", {"hero"}))

  local output = {hero}
  local section = ""
  local i = 4
  while i <= #blocks do
    local block = blocks[i]
    if block.t == "Header" and block.level == 2 then
      section = stringify(block)
      table.insert(output, block)
      i = i + 1
    elseif block.t == "Header" and block.level == 3 then
      local dates, details = split_heading(block.content)
      local heading = pandoc.Header(3, {
        pandoc.Span(dates, pandoc.Attr("", {"dates"})),
        pandoc.Span(details, pandoc.Attr("", {"details"})),
      })
      local grouped = {heading}
      i = i + 1
      while i <= #blocks and not (blocks[i].t == "Header" and blocks[i].level <= 3) do
        table.insert(grouped, blocks[i])
        i = i + 1
      end
      local class = section == "Work experience" and "experience" or "credential"
      table.insert(output, pandoc.Div(grouped, pandoc.Attr("", {class})))
    else
      table.insert(output, block)
      i = i + 1
    end
  end

  doc.blocks = output
  return doc
end

local function styled_paragraph(inlines, style)
  return pandoc.Div({pandoc.Para(inlines)}, pandoc.Attr("", {}, {{"custom-style", style}}))
end

local function styled_inlines(inlines, style)
  return {pandoc.Span(inlines, pandoc.Attr("", {}, {{"custom-style", style}}))}
end

local function accent_strong(block)
  return pandoc.walk_block(block, {
    Strong = function(strong)
      return pandoc.Span(strong.content, pandoc.Attr("", {}, {{"custom-style", "Strong"}}))
    end,
  })
end

local function docx_table(rows)
  local simple = pandoc.SimpleTable(
    {},
    {pandoc.AlignLeft, pandoc.AlignLeft},
    {0.13, 0.87},
    {},
    rows
  )
  return pandoc.utils.from_simple_table(simple)
end

local function docx_document(doc)
  local blocks = doc.blocks
  if #blocks < 3 or blocks[1].t ~= "Header" or blocks[1].level ~= 1 then
    error("cv.md must begin with a level-one name heading, role, and contact line")
  end

  if stringify(blocks[1]) ~= "Igor Makarov" then
    error("Expected the CV title to be Igor Makarov")
  end
  local title_inlines = tracked_title("docx")
  title_inlines:insert(pandoc.Span(unwrap_strong(blocks[2]), pandoc.Attr("", {}, {{"custom-style", "Subtitle Char"}})))

  for index = 3, #blocks do
    blocks[index] = accent_strong(blocks[index])
  end

  local contact = blocks[3]
  local output = {
    styled_paragraph(title_inlines, "Title"),
    pandoc.Div({contact}, pandoc.Attr("", {}, {{"custom-style", "Style1"}})),
  }

  local i = 4
  while i <= #blocks do
    local block = blocks[i]
    if block.t == "Header" and block.level == 2 then
      local section = stringify(block)
      table.insert(output, pandoc.Header(1, block.content))
      i = i + 1

      if section == "Work experience" or section == "Professional courses" or section == "Diplomas" then
        local rows = {}
        while i <= #blocks and not (blocks[i].t == "Header" and blocks[i].level == 2) do
          if blocks[i].t ~= "Header" or blocks[i].level ~= 3 then
            error("Expected a level-three dated item in " .. section)
          end
          local dates, details = split_heading(blocks[i].content)
          i = i + 1
          local right = {styled_paragraph(details, "No Spacing")}
          while i <= #blocks and not (blocks[i].t == "Header" and blocks[i].level <= 3) do
            if blocks[i].t == "Para" then
              table.insert(right, styled_paragraph(blocks[i].content, "No Spacing"))
            else
              table.insert(right, blocks[i])
            end
            i = i + 1
          end
          table.insert(rows, {
            {styled_paragraph(styled_inlines(dates, "Dates Char"), "No Spacing")},
            right,
          })
        end
        table.insert(output, docx_table(rows))
      end
    else
      table.insert(output, block)
      i = i + 1
    end
  end

  table.insert(output, styled_paragraph({pandoc.Str("​")}, "Table End"))
  doc.blocks = output
  return doc
end

function Pandoc(doc)
  if FORMAT:match("html") then
    return html_document(doc)
  end
  if FORMAT == "docx" then
    return docx_document(doc)
  end
  return doc
end
