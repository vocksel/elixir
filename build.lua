
--[[
  This is Elixir. It compiles everything under the source directory into a
  ROBLOX compatible XML file that you can drag-and-drop into your game.

  You'll need a Lua interpreter and the LuaFileSystem module installed to run
  this file. In Windows this can be done by installing LuaForWindows[1], which
  comes bundled with LuaFileSystem.

  [1] https://code.google.com/p/luaforwindows/
--]]

local lfs = require "lfs"

if _VERSION == "Lua 5.2" then
  unpack = table.unpack
end





--[[
  Configuration
  ==============================================================================
--]]

--[[
  An array of files to ignore when compiling the source code.

  .gitignore is used extensively to allow us to commit directories. This makes
  it easier for new users to get started, so they aren't required to create a
  bunch of directories.
--]]
local IGNORED = {
  ".gitignore"
}

--[[
  Where source code is stored and compiled to, respectively.
--]]
local SOURCE_DIR = "source"
local BUILD_DIR  = "build"

--[[
  The name and extension of the Model file that will be generated.

  [1] Roblox only supports two extensions: rbxm and rbxmx. The former uses
      binary while the latter uses XML. Because this build only compiles to
      XML, the rbxmx file extension is prefered.
--]]
local RBXM_FILE_NAME = "elixir"
local RBXM_FILE_EXT  = ".rbxmx" -- [1]
local RBXM_FILE = RBXM_FILE_NAME..RBXM_FILE_EXT

--[[
  Sets the name for the top-most instance in the model file. This contains all
  of the descendants of the source directory, once they're compiled.
--]]
local RBXM_ROOT_NAME  = "elixir"

--[[
  The instance that will be used to replicate the folder structure. Any
  instance can be used, but Folders are recommended.
--]]
local CONTAINER_CLASS = "Configuration"





--[[
  Helpers
  ==============================================================================
--]]

function isDir(dir)
  return lfs.attributes(dir, "mode") == "directory"
end

local function isNotIgnored(filename)
  if filename ~= ".." and filename ~= "." then
    for _,ignoredFile in ipairs(IGNORED) do
      if filename ~= ignoredFile then
        return true
      end
    end
  end
  return false
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

local xml = {
  -- Characters that need to be escaped before being added to the XML string.
  escapeChars = {
    ["\""] = "quot",
    ["&"]  = "amp",
    ["'"]  = "apos",
    ["<"]  = "lt",
    [">"]  = "gt"
  }
}

--[[
  Create a new XML object. Each instance has a 'contents' property which
  contains each line of XML you write to it as a string.

  The strings in 'contents' are later concatenated together to be output
  to a file.

    local test = xml:new()
      :ln():append("<name>")
      :ln():indent(1):append("<first>John</first>")
      :ln():indent(1):append("<last>Smith</last>")
      :ln():append("</name>")

    -- <name>
    --   <first>John</first>
    --   <last>Smith</last>
    -- </name>

  [2] This value is incremented when inside of a loop to allow child elements to
      make use of the same code, while still indenting them more than the
      previous elements.

      Remember to always set it back to 0 after the loop, otherwise you could
      run into some indenting issues.

      Example:

        local file = xml:new()
        file.indentLevel = 1
        file:ln():indent(1):append("<Test></Test>") -- "\n\t\t<Test></Test>"

      It applied two tabs because it's adding the number passed to indent() with
      the indentLevel.
--]]
function xml:new()
  local obj = {
    contents = {},
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
  local out = ""
  for i = 1, #str do
    local char = str:sub(i,i)
    if self.escapeChars[char] then
      char = "&"..self.escapeChars[char]..";"
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
      :ln():indent(1):append("<Test></Test>") -- "\n\t<Test></Test>"
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
      <Item class="Script">                   -- xml:indent(1)
        <Properties>                          -- xml:indent(2)
          <string name="Name">Script</string> -- xml:indent(3)
          ...
        </Properties>                         -- xml:indent(1)
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
  Data Type Encoding
  ==============================================================================
--]]

--[[
  These methods encode Lua and Roblox data types into XML-safe strings. They are
  run dynamically by rbxm:encodeProperty.
--]]

local encode = {}


function encode.bool(data)
  return not not data
end

function encode.double(data)
  string.format("%f", data)
end

function encode.int(data)
  return string.format("%i", data)
end

function encode.string(data)
  return xml:encodeTruncEsc(xml:escape(data))
end

function encode.ProtectedString(data)
  return xml:encodeTruncEsc(xml:escape(data))
end





--[[
  Roblox Models
  ==============================================================================
--]]

local rbxm = {}

--[[
  Create a Value instance (Int, String, Bool, etc).

  @param string className  Any Roblox "Value" instance. StringValue, BoolValue,
                           etc.
  @param string name       Name of the Value
  @param any    value      Depends on which instance you use. If you're using a
                           StringValue then this must be a string.
--]]
function rbxm:createValue(className, name, value)
  return {
    ClassName = className .. "Value",
    Name = { "string", name },
    Value = { className:lower(), value }
  }
end

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
  Uses methods in the 'encode' object to convert Roblox properties into XML-safe
  strings.

  @param className The ClassName of the property. CFrame, Ray and UDim2 would
                   all be applicable.
  @param value     The value to be encoded.
--]]
function rbxm:encodeProperty(className, value)
  if encode[className] then
    value = encode[className](value)
  end
  return value
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
  if type(object) ~= "table" then
    error("table expected", 2)
  end

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
  if type(var) == "table" then
    var = self:tabToStr(var)
  end
  if type(var) == "string" then
    local file = assert(io.open(filename, "w"))
    file:write(var)
    file:flush()
    file:close()
  else
    error("bad type", 2)
  end
end





--[[
  Compiling
  ==============================================================================
--]]

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
local function getEmbeddedProperties(path)
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
  if next(props) == nil then -- [1]
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
local function handleFile(path, file)
  local props = getEmbeddedProperties(path)
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

local function recurseDir(path, obj)
  print("DIR", path)
  for name in lfs.dir(path) do
    if isNotIgnored(name) then
      local joined = path.."/"..name

      local dir = {
        ClassName = CONTAINER_CLASS,
        Name = { "string", name }
      }

      if isDir(joined) then
        obj[#obj+1] = recurseDir(joined, dir, true)
      else
        print("FILE", joined)
        obj[#obj+1] = handleFile(joined, name)
      end
    end
  end
  return obj
end

--[[
  Compile the directory structure and the source code into a Roblox-compatible
  file. Configure the paths and filenames at the top of this file.

  @param String args
    Arguments from the command-line. Only supports one argument, which alters
    the path that the model file is built to.
--]]
function compile(args)
  local rbxmObj = recurseDir(SOURCE_DIR, {
    ClassName = CONTAINER_CLASS,
    Name = { "string", RBXM_ROOT_NAME }
  })

  local rbxmPath = BUILD_DIR.."/"..(args[1] or RBXM_FILE)

  lfs.mkdir(BUILD_DIR)
  rbxm:save(rbxmObj, rbxmPath)
end

compile({...})
