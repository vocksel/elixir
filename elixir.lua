
--[[
  This is Elixir. It compiles everything under the source directory into a
  ROBLOX compatible XML file that you can drag-and-drop into your game.

  You'll need a Lua interpreter and the LuaFileSystem module installed to run
  this file. In Windows this can be done by installing LuaForWindows[1], which
  comes bundled with LuaFileSystem.

  [1] https://code.google.com/p/luaforwindows/
--]]

local elixir = {
  _VERSION = "v0.2.0",
  _URL = "https://github.com/voxeldavid/elixir",
  _DESCRIPTION = "Elixir is a build system for ROBLOX that compiles Lua code into an XML file",
  _LICENSE = [[
    This is free and unencumbered software released into the public domain.

    Anyone is free to copy, modify, publish, use, compile, sell, or
    distribute this software, either in source code form or as a compiled
    binary, for any purpose, commercial or non-commercial, and by any
    means.

    In jurisdictions that recognize copyright laws, the author or authors
    of this software dedicate any and all copyright interest in the
    software to the public domain. We make this dedication for the benefit
    of the public at large and to the detriment of our heirs and
    successors. We intend this dedication to be an overt act of
    relinquishment in perpetuity of all present and future rights to this
    software under copyright law.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

    For more information, please refer to [http://unlicense.org]
  ]]
}

local lfs = require "lfs"

if _VERSION == "Lua 5.2" then
  unpack = table.unpack
end





--[[
  Helpers
  ==============================================================================
--]]

function isDir(dir)
  return lfs.attributes(dir, "mode") == "directory"
end

local function splitName(path)
  for i = #path, 1, -1 do
    local c = path:sub(i, i)
    if c == "." then
      return path:sub(1, i-1), path:sub(i+1, #path)
    end
  end
  return path, ""
end

-- Extract the contents of a file
local function getFileContents(path)
  local file = assert(io.open(path))
  local content = file:read("*a")
  file:close()

  return content
end





--[[
  XML
  ==============================================================================
--]]

local xml = {}

--[[
  Create a new XML object. Each instance has a 'contents' property which
  contains each line of XML you write to it as a string.

  The strings in 'contents' are later concatenated together to be output
  to a file.

    local test = xml:new()
      :ln():append("<name>")
      :ln():ind(1):append("<first>John</first>")
      :ln():ind(1):append("<last>Smith</last>")
      :ln():append("</name>")

    -- <name>
    --   <first>John</first>
    --   <last>Smith</last>
    -- </name>

  [1] 'contents' is where all of the XML strings are stored, before lating being
      concatenated into a single string.

  [2] This value is incremented when inside of a loop to allow child elements to
      make use of the same code, while still indenting them more than the
      previous elements.

      Remember to always set it back to 0 after the loop, otherwise you could
      run into some indenting issues.

      Example:

        local file = xml:new()
        file.indentLevel = 1
        file:ln():ind(1):append("<Test></Test>") -- "\n\t\t<Test></Test>"

      It applied two tabs because it's adding the number passed to ind() with th
      indentLevel.
--]]
function xml:new()
  local obj = {
    contents = {}, -- [1]
    indentLevel = 0 -- [2]
  }
  setmetatable(obj, self)
  self.__index = self
  return obj
end

--[[
  Because of the way XML is parsed, leading spaces get truncated. So simply add
  a "\" when a space or "\" is detected as the first character. This will be
  decoded automatically by Cure
--]]
function xml:encodeTruncEsc(str)
  local first = str:sub(1,1)
  if first:match("%s") or first == "\\" then
    return "\\"..str
  end
  return str
end

--[[
  Certain characters need to be escaped to work properly in the XML. Because XML
  uses < and > to denote tags, they have to be escaped to &lt; and &gt; for use
  in properties and scripts.
--]]
function xml:escape(str)
  local escapeChars = {
    ["\""] = "quot",
    ["&"]  = "amp",
    ["'"]  = "apos",
    ["<"]  = "lt",
    [">"]  = "gt"
  }
  local out = ""
  for i = 1, #str do
    local char = str:sub(i,i)
    if escapeChars[char] then
      char = "&"..escapeChars[char]..";"
    elseif not char:match("^[\10\13\32-\126]$") then
      char = "&#"..char:byte()..";"
    end
    out = out..char
  end
  return out
end

--[[
  Append the arguments onto the self.contents table. Later on, all the appended
  strings are concatenated into a single string, which gets turned into an XML
  file.
--]]
function xml:append(...)
  local args = {...}

  local function concat(arg)
    if type(arg) == "table" then
      concat(unpack(arg))
    else
      self.contents[#self.contents+1] = tostring(arg)
    end
  end

  for i = 1, #args do
    concat(args[i])
  end

  return self
end

--[[
  Used at the beginning of an XML chain to start everything off on a newline.

  Example:

    xml:new()
      :ln():ind(1):append("<Test></Test>") -- "\n\t<Test></Test>"
--]]
function xml:ln()
  self:append("\n")
  return self
end

--[[
  Indents a line to make reading the XML easier. Who wants to read unindented
  markup?

  Example:

    <roblox ...>
      <Item class="Script">                   -- xml:ind(1)
        <Properties>                          -- xml:ind(2)
          <string name="Name">Script</string> -- xml:ind(3)
          ...
        </Properties>                         -- xml:ind(1)
      </Item>
    </roblox>

  @param number indentSize Number of times you want to indent the next lines.
--]]
function xml:ind(indentSize)
  local scope = self.indentLevel
  if scope then
    self:append(string.rep("\t", scope+indentSize))
  else
    self:append(string.rep("\t", indentSize))
  end
  return self
end

--[[
` Merges all of the loose XML strings together for exporting to a file.
--]]
function xml:save()
  return table.concat(self.contents)
end





--[[
  Roblox Models
  ==============================================================================
--]]

local rbxm = {}

--[[
  Generate a new Script instance.

  @param string className  Type of script. Eg. "Script" or "LocalScript"
  @param string name       Name of the script
  @param string source     The Lua source of the script
  @param bool   disabled   If the script can run automatically
--]]
function rbxm:createScript(className, name, source, disabled)
  local obj = {
    ClassName = className;
    Name = { "string", name };
    Source = { "ProtectedString", source };
  }

  if disabled then
    obj.Disabled = { "bool", true };
  end

  return obj
end

--[[
  Lua files are checked for syntax errors.

  Note:
  - A file with an error will still be compiled regardless.
  - It doesn't care about anything undefined. It only checks for syntax errors,
    so you're free to use 'game' and 'workspace' in your code.
--]]
function rbxm:checkScriptSyntax(source)
  local func, err = loadstring(source, "")
  if not func then
    print("WARNING: " .. err:gsub("^%[.-%]:", "line "))
  end
end

--[[
  The "referent" attribute is applied to every <Item> tag, and is used as a
  unique identifier for each instance in the game.

  This function simply increments a value so we can be sure we always use a
  unique number as the referent.
--]]
function rbxm:referent()
  local ref = 0
  return function()
    ref = ref + 1
    return ref
  end
end

--[[
  Encodes Lua and Roblox data types into XML-safe strings.

  @param datatype  The ClassName of the property.
  @param value     The value to be encoded.
--]]
function rbxm:encodeProperty(datatype, value)
  if datatype == "bool" then
    return not not value

  elseif datatype == "double" then
    return string.format("%f", value)

  elseif datatype == "int" then
    return string.format("%i", value)

  elseif datatype == "string" or datatype == "ProtectedString" then
    return xml:escape(value)
  end
end

--[[
  Extract the properties from an instance.

  @param table object A table contaiing key/value pairs that replicate the
                      properties of a Roblox instance.

  [1] The ClassName is applied as an XML attribute and must be omitted from the
      list of properties.
  [2] Keep everything consistent by sorting the properties.
--]]
function rbxm:getProperties(object)
  local sorted = {}
  for k in pairs(object) do
    if type(k) == "string" and k ~= "ClassName" then -- [1]
      sorted[#sorted+1] = k
    end
  end
  table.sort(sorted) -- [2]
  return sorted
end

--[[
  Creates the body of the XML file. All of the Item tags with their properties
  are generated by this method.

  @param table object Tabularized directory structure that will be converted
                      into XML.
--]]
function rbxm:body(object)
  local body = xml:new()
  local ref = self:referent()

  local function exportProperties(object)
    local props = rbxm:getProperties(object)

    for i = 1, #props do
      local name      = props[i]
      local className = object[name][1]
      local value     = object[name][2]

      value = self:encodeProperty(className, value)
      body:ln():ind(2):append(string.format("<%s name=\"%s\">%s</%s>", className, name, value, className))
    end
  end

  local function writeXML(object)
    body:ln():ind(0):append(string.format("<Item class=\"%s\" referent=\"RBX%s\">", object.ClassName, ref()))
    body:ln():ind(1):append("<Properties>")
    exportProperties(object)
    body:ln():ind(1):append("</Properties>")
    for i = 1, #object do
      body.indentLevel = body.indentLevel + 1
      writeXML(object[i])
      body.indentLevel = body.indentLevel - 1
    end
    body:ln():ind(0):append("</Item>")
  end

  body.indentLevel = body.indentLevel + 1
  writeXML(object)

  return body:save()
end

--[[
  Runs tasks to compile the directory structure into an XML file.

  @param table object Tabularized directory structure that will be converted
                      into XML.
--]]
function rbxm:tabToStr(object)
  local body = self:body(object)
  local file = xml:new()
  file:append("<roblox "..
    "xmlns:xmime=\"http://www.w3.org/2005/05/xmlmime\" "..
    "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "..
    "xsi:noNamespaceSchemaLocation=\"http://www.roblox.com/roblox.xsd\" "..
    "version=\"4\">")
  file:append(body)
  file:ln():append("</roblox>")

  return file:save()
end

-- Saves an RBXM string or table.
function rbxm:save(var, filename)
  local file = assert(io.open(filename, "w"))
  file:write(self:tabToStr(var))
  file:flush()
  file:close()
end





--[[
  Compiler
  ==============================================================================
--]]

local Compiler = {}
Compiler.__index = Compiler

function Compiler.new(obj)
  local obj = obj or {}
  return setmetatable(obj, Compiler)
end

--[[
  Skips a file when compiling if it's in the list of ignored files.

  @param table list      Array containing all of the filesnames to ignore.
  @param string filename Name of the file, not the full path. If there are any
    slashes then you are not passing in the filename.
--]]
function Compiler:isIgnored(filename)
  if filename == "." or filename == ".." then
    return true
  end
  if next(self.ignored) then -- List of ignored files can be empty
    for _,ignoredFile in ipairs(self.ignored) do
      if filename == ignoredFile then
        return true
      end
    end
  end
  return false
end

--[[
  This function allows you to embed Roblox properties at the top of a file using
  inline comments.

  Normally when you create a file, you would include the class in the filename.
  Something like "player-entered.script.lua". This would generate a new Script
  named "player-entered".

  Embedded properties allow you to define the Name, ClassName, and other
  properties, at the top of the file.

  If we had a file named "boring-script.module.lua" with the following contents:

    -- Name: SomeCoolScript
    -- ClassName: LocalScript

    [code]

  Then a LocalScript named SomeCoolScript would be created. Note that embedded
  properties take precedence over filename properties.

  @param string path Full path to the Lua file. The contents are read for
                     embedded properties.

  [1] No embedded properties were found in the file.
--]]
function Compiler:getEmbeddedProperties(path)
  local props = {}
  local pattern = "^--%s(%w+):%s(%w+)"
  for line in io.lines(path) do
    if not line:match("^[--]+") then
      break
    end
    for k,v in line:gmatch(pattern) do
      props[k] = v
    end
  end
  if not next(props) then -- [1]
    return
  end
  return props
end

--[[
  Run functions for specific types of files.

  @param string path Full path to the current file. LFS needs this to read the
                     file.
  @param string file Name and extension of the file.

  [1] If the properties are not embedded we derive them from the file name.
  [2] The class name is only used for comparisons, so we can lower-case it to
      allow for case insensitivity when setting the class.
--]]
function Compiler:handleFile(path, file)
  local props = self:getEmbeddedProperties(path)
  local content = getFileContents(path)
  local baseName, ext = splitName(file)
  local name, className = splitName(baseName)

  if props then
    name = props.Name or name -- [1]
    className = props.ClassName or className -- [1]
  end

  ext = ext:lower()
  className = className:lower() -- [2]

  if ext == "lua" then
    rbxm:checkScriptSyntax(content)
    if className == "localscript" or className == "local" then
      return rbxm:createScript("LocalScript", name, content)
    elseif className == "modulescript" or className == "module" then
      return rbxm:createScript("ModuleScript", name, content)
    else
      return rbxm:createScript("Script", name, content)
    end
  end
end

function Compiler:recurseDir(path, obj)
  print("DIR", path)
  for name in lfs.dir(path) do
    if not self:isIgnored(name) then
      local joined = path.."/"..name

      local dir = {
        ClassName = self.rbxClass,
        Name = { "string", name }
      }

      if isDir(joined) then
        obj[#obj+1] = self:recurseDir(joined, dir, true)
      else
        print("FILE", joined)
        obj[#obj+1] = self:handleFile(joined, name)
      end
    end
  end
  return obj
end

--[[
  Compile the directory structure and the source code into a Roblox-compatible
  file. Configure the paths and filenames at the top of this file.
--]]
function Compiler:compile()
  local rbxmObj = self:recurseDir(self.source, {
    ClassName = self.rbxClass,
    Name = { "string", self.rbxName }
  })

  local rbxmPath = self.build.."/"..self.fileName..self.fileExt

  lfs.mkdir(self.build)
  rbxm:save(rbxmObj, rbxmPath)
end





--[[
  Elixir
  ==============================================================================
--]]

function elixir.elixir(options)
  local options = options or {}
  local file = Compiler.new{
    source   = options.source   or "source",
    build    = options.build    or "build",
    fileName = options.fileName or "elixir",
    fileExt  = options.fileExt  or ".rbxmx",
    rbxName  = options.rbxName  or "Elixir",
    rbxClass = options.rbxClass or "Configuration",
    ignored  = options.ignored  or {}
  }
  file:compile()
end

setmetatable(elixir, { __call = function(_, ...) return elixir.elixir(...) end })

return elixir
