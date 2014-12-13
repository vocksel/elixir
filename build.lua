
--[[
  This is Cure's build file. It compiles everything under the source directory
  into a Roblox-compatible XML file that you can drag-and-drop into your game.

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
  Array of alternative paths to output the contents of the model. You must
  specify the full file path and extension.
--]]
local LOCATIONS = {
  -- "output.rbxmx",
  -- "test/game.rbxmx"
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
local RBXM_FILE_NAME = "cure"
local RBXM_FILE_EXT  = ".rbxmx" -- [1]
local RBXM_FILE = RBXM_FILE_NAME..RBXM_FILE_EXT

--[[
  Sets the name for the top-most instance in the model file. This contains all
  of the descendants of the source directory, once they're compiled.
--]]
local RBXM_ROOT_NAME  = "cure"

--[[
  The instance that will be used to replicate the folder structure. Any
  instance can be used, but Folders are recommended.
--]]
local CONTAINER_CLASS = "Configuration"

-- maximum length of strings in replicated instances
local MAX_STRING_LENGTH = 200000 - 1





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

function encode.CoordinateFrame(data)
  local d = { data:components() }

  return xml:neW()
    :ln():ind(1):append(("<X>"..d[1].."</X>"))
    :ln():ind(1):append(("<Y>"..d[2].."</Y>"))
    :ln():ind(1):append(("<Z>"..d[3].."</Z>"))
    :ln():ind(1):append(("<R00>"..d[4].."</R00>"))
    :ln():ind(1):append(("<R01>"..d[5].."</R01>"))
    :ln():ind(1):append(("<R02>"..d[6].."</R02>"))
    :ln():ind(1):append(("<R10>"..d[7].."</R10>"))
    :ln():ind(1):append(("<R11>"..d[8].."</R11>"))
    :ln():ind(1):append(("<R12>"..d[9].."</R12>"))
    :ln():ind(1):append(("<R20>"..d[10].."</R20>"))
    :ln():ind(1):append(("<R21>"..d[11].."</R21>"))
    :ln():ind(1):append(("<R22>"..d[12].."</R22>"))
    :save()
end

function encode.Color3(data)
  return tonumber(string.format("0xFF%02X%02X%02X", data.r*255, data.g*255, data.b*255))
end

function encode.Content(data)
  if #data == 0 then
    return "<null></null>"
  else
    return { "<url>"..data.."</url>" }
  end
end

function encode.Ray(data)
  local o = data.Origin
  local d = data.Direction
  return xml:new()
    :ln():ind(1):append("<origin>")
    :ln():ind(2):append("<X>", o.x, "</X>")
    :ln():ind(2):append("<Y>", o.y, "</Y>")
    :ln():ind(2):append("<Z>", o.z, "</Z>")
    :ln():ind(1):append("</origin>")
    :ln():ind(1):append("<direction>")
    :ln():ind(2):append("<X>", d.x, "</x>")
    :ln():ind(2):append("<Y>", d.y, "</Y>")
    :ln():ind(2):append("<Z>", d.z, "</Z>")
    :ln():ind(1):append("</direction>")
    :save()
end

function encode.Vector3(data)
  return xml:new()
    :ln():ind(1):append("<X>"..data.x.."</X>")
    :ln():ind(1):append("<Y>"..data.y.."</Y>")
    :ln():ind(1):append("<Z>"..data.z.."</Z>")
    :save()
end

function encode.Vector2(data)
  return xml:new()
    :ln():ind(1):append("<X>"..data.x.."</X>")
    :ln():ind(1):append("<Y>"..data.y.."</Y>")
    :save()
end

function encode.UDim2()
  return xml:new()
    :ln():ind(1):append("<XS>"..data.X.Scale.."</XS>")
    :ln():ind(1):append("<XO>"..data.X.Offset.."</XO>")
    :ln():ind(1):append("<YS>"..data.Y.Scale.."</YS>")
    :ln():ind(1):append("<YO>"..data.Y.Offset.."</YO>")
    :save()
end

function encode.Ref(data)
  if data == nil then
    return "null"
  else
    return data
  end
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
  Generate a new Script instance. Wrappers for this method are found below it.

  The wrappers only serve to pass in the className argument for you. When using
  one, you only need to specify name, source and disabled

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

function rbxm:createServerScript(...)
  return self:createScript("Script", ...)
end

function rbxm:createLocalScript(...)
  return self:createScript("LocalScript", ...)
end

--[[
  Create an IntValue containing the ID of a Roblox asset. Things like Models,
  Decals and T-Shirts are all assets, and you can find their ID at the end of
  the URL.

  @param string name  Name of the value
  @param number value ID of a Roblox asset. The number at the end of the URL on
                      an item. Eg. 42891177, 40469899, 39053953
--]]
function rbxm:createAsset(file, name, value)
  value = tonumber(value)
  if not value then
    print("WARNING: content of '"..file.."' must be a number")
  end
  return self:createValue("Int", name, value)
end

--[[
  Split apart the contents of the file into multiple StringValues, contained
  inside a BoolValue.

  Example (varies, depending on size):

    extremely-large-file.lua

  Turns into:

    extremely-large-file
    - 1
    - 2
    - 3
    - etc.
--]]
function rbxm:splitFileParts(content)
  local chunk = MAX_STRING_LENGTH
  local length = #content
  local container = rbxm:createValue("Bool", name, true)

  for i = 1, math.ceil(length/chunk) do
    local a = (i - 1)*chunk + 1
    local b = a + chunk - 1
    b = b > length and length or b
    container[i] = rbxm:createValue("String", tostring(i), content:sub(a, b))
  end

  return container
end

--[[
  Lua files are checked for syntax errors. Note that a file with an error will
  still be built regardless.
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
  Run functions for specific types of files.

  @param string path       Full path to the current file. LFS needs this to read
                           the file.
  @param string file       Name and extension of the file.
  @param bool   subfolder  Cure's scripts live in the root of the source dir, if
                           'subfolder' is true it's safe to assume that the
                           following scripts belong to Cure.
--]]
local function handleFile(path, file, subfolder)
  local content = getFileContents(path)
  local name, extension = splitName(file)
  local subName, subExtension = splitName(name)

  extension = extension:lower()
  subExtension = subExtension:lower()

  -- Special handling for the main Cure scripts
  if not subfolder then
    rbxm:checkScriptSyntax(content)

    if file:lower() == "cure.server.lua" then
      return rbxm:createServerScript("cure.server", content)
    elseif file:lower() == "cure.client.lua" then
      return rbxm:createLocalScript("cure.client", content)
    end
  end

  if extension == "lua" then
    rbxm:checkScriptSyntax(content)

    if subExtension == "script" then
      return rbxm:createServerScript(subName, content)
    elseif subExtension == "localscript" then
      return rbxm:createLocalScript(subName, content)
    else
      local chunk = MAX_STRING_LENGTH
      local length = #content

      if length <= chunk then
        -- Create a StringValue to hold the source of the file
        return rbxm:createValue("String", name, content)
      else
        -- If the file is too big, split it into multiple parts
        return rbxm:splitFileParts(content)
      end
    end
  elseif extension == "asset" then
    -- Create an IntValue containing a Roblox AssetID
    return rbxm:createAsset(file, name, content)
  else
    -- Disable and comment out anything else
    return rbxm:createServerScript(name, "--[==[\n"..content.."\n--]==]", true)
  end
end

local function recurseDir(path, obj, recurse)
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
        obj[#obj+1] = handleFile(joined, name, recurse)
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

  for i,v in ipairs(LOCATIONS) do
    rbxm:save(rbxmObj, LOCATIONS[i])
  end
end

compile({...})
