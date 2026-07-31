-- Convert fenced code to wrap-capable paragraphs inside one semantic Code tag.
-- This avoids tagging-incompatible listings/fvextra packages while preserving
-- line breaks and indentation in the printable guide.

local function horizontal_space(count)
  return pandoc.RawInline(
    "latex",
    string.format(
      "\\hspace*{\\dimexpr%d\\fontdimen2\\font\\relax}",
      count
    )
  )
end

local function code_line(text)
  text = text:gsub("\t", "    ")
  if text == "" then
    return pandoc.Para({pandoc.RawInline("latex", "\\strut")})
  end

  local inlines = {}
  local cursor = 1
  while cursor <= #text do
    local first, last = text:find(" +", cursor)
    if not first then
      table.insert(inlines, pandoc.Str(text:sub(cursor)))
      break
    end
    if first > cursor then
      table.insert(inlines, pandoc.Str(text:sub(cursor, first - 1)))
    end
    local count = last - first + 1
    if #inlines == 0 then
      table.insert(inlines, horizontal_space(count))
    else
      table.insert(inlines, pandoc.Space())
      if count > 1 then
        table.insert(inlines, horizontal_space(count - 1))
      end
    end
    cursor = last + 1
  end
  return pandoc.Para(inlines)
end

function CodeBlock(block)
  local blocks = {
    pandoc.RawBlock("latex", "\\begin{GuideCode}"),
  }
  for line in (block.text .. "\n"):gmatch("(.-)\n") do
    table.insert(blocks, code_line(line))
  end
  table.insert(blocks, pandoc.RawBlock("latex", "\\end{GuideCode}"))
  return blocks
end
