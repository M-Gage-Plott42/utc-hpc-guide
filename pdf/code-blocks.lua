-- Convert fenced code to wrap-capable paragraphs inside one semantic Code tag.
-- This avoids tagging-incompatible listings/fvextra packages while preserving
-- line breaks and indentation in the printable guide.

local image_widths = {
  ["ood_desktop_request_form_sanitized.png"] = "84%",
  ["ood_session_card_sanitized.png"] = "78%",
  ["ood_storage_shortcuts_sanitized.png"] = "52%",
}

local function horizontal_space(count)
  return pandoc.RawInline(
    "latex",
    string.format(
      "\\hspace*{\\dimexpr%d\\fontcharwd\\font`0\\relax}",
      count
    )
  )
end

local function code_rail()
  -- Enter horizontal mode before opening the layout artifact. This keeps the
  -- rail on the source-line paragraph instead of creating an empty paragraph.
  return pandoc.RawInline("latex", "\\leavevmode\\GuideCodeRail{}")
end

local function code_line(text)
  text = text:gsub("\t", "    ")
  if text == "" then
    return pandoc.Para({code_rail(), pandoc.RawInline("latex", "\\strut")})
  end

  local source_inlines = {}
  local cursor = 1
  while cursor <= #text do
    local first, last = text:find(" +", cursor)
    if not first then
      table.insert(source_inlines, pandoc.Str(text:sub(cursor)))
      break
    end
    if first > cursor then
      table.insert(source_inlines, pandoc.Str(text:sub(cursor, first - 1)))
    end
    local count = last - first + 1
    if #source_inlines == 0 then
      table.insert(source_inlines, horizontal_space(count))
    else
      table.insert(source_inlines, pandoc.Space())
      if count > 1 then
        table.insert(source_inlines, horizontal_space(count - 1))
      end
    end
    cursor = last + 1
  end
  local inlines = {code_rail()}
  for _, inline in ipairs(source_inlines) do
    table.insert(inlines, inline)
  end
  return pandoc.Para(inlines)
end

local function code_lines(text)
  if text == "" then
    error("fenced code block must contain at least one source line")
  end
  if text:sub(1, 1) == "\n" or text:sub(-1) == "\n" then
    error("fenced code block has a leading or trailing blank source line")
  end
  local lines = {}
  for line in (text .. "\n"):gmatch("(.-)\n") do
    table.insert(lines, line)
  end
  return lines
end

function CodeBlock(block)
  local blocks = {
    pandoc.RawBlock("latex", "\\begin{GuideCode}"),
  }
  for _, line in ipairs(code_lines(block.text)) do
    table.insert(blocks, code_line(line))
  end
  table.insert(blocks, pandoc.RawBlock("latex", "\\end{GuideCode}"))
  return blocks
end

-- Keep responsive Markdown sources presentation-neutral while applying the
-- reviewed printable-guide scale to the three sanitized screenshots. Image
-- content and normal alternative text remain owned by the Markdown source.
function Image(image)
  local filename = image.src:match("([^/]+)$")
  local width = image_widths[filename]
  if width then
    image.attributes.width = width
  end
  return image
end

-- Inline code in a Markdown heading is literal title text, not a terminal
-- sample. Keep the source AST presentation-neutral, but let the PDF heading
-- and contents entry inherit the standard Noto heading face.
function Header(header)
  if not FORMAT:match("latex") then
    return nil
  end
  header.content = header.content:walk({
    Code = function(code)
      return pandoc.Str(code.text)
    end,
  })
  return header
end

-- Keep each bounded chapter opener (H1 through its first H2) together with
-- core LaTeX page-breaking controls. The emitted section commands remain the
-- standard tagging-aware commands; no heading or box package is involved.
function Pandoc(document)
  if not FORMAT:match("latex") then
    return nil
  end

  local blocks = pandoc.Blocks({})
  local opener = nil
  for _, block in ipairs(document.blocks) do
    if block.t == "Header" and block.level == 1 then
      if opener then
        error("chapter opener is missing its first level-two heading")
      end
      opener = {
        title = pandoc.utils.stringify(block.content),
        first_body_seen = false,
        intro_seen = false,
      }
      blocks:insert(pandoc.RawBlock("latex", "\\begin{samepage}"))
      blocks:insert(block)
    elseif opener and not opener.first_body_seen then
      if block.t == "RawBlock" then
        blocks:insert(block)
      elseif block.t ~= "Para" then
        error(
          "chapter opener must begin with a short introductory paragraph: "
            .. opener.title
        )
      else
        opener.first_body_seen = true
        opener.intro_seen = true
        blocks:insert(block)
      end
    elseif opener and block.t == "Header" and block.level == 2 then
      if not opener.intro_seen then
        error("chapter opener is missing its introductory paragraph: " .. opener.title)
      end
      blocks:insert(block)
      blocks:insert(pandoc.RawBlock("latex", "\\end{samepage}"))
      blocks:insert(pandoc.RawBlock("latex", "\\nopagebreak[4]"))
      opener = nil
    else
      blocks:insert(block)
      if block.t == "Header" and block.level == 2 then
        blocks:insert(pandoc.RawBlock("latex", "\\nopagebreak[4]"))
      end
    end
  end

  if opener then
    error("chapter opener is missing its first level-two heading: " .. opener.title)
  end
  document.blocks = blocks
  return document
end
