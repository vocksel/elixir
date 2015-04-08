
-- This is Elixir. It compiles everything under the source directory into a
-- ROBLOX compatible XML file that you can drag-and-drop into your game.
--
-- You'll need a Lua interpreter and the LuaFileSystem module installed to run
-- this file. In Windows this can be done by installing LuaForWindows[1], which
-- comes bundled with LuaFileSystem.
--
-- [1] https://code.google.com/p/luaforwindows/

local elixir = {
  _VERSION = "v0.3.0",
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

local lfs = require("lfs")

-- Default options for Elixir. It's best to configure these dynamically when
-- calling Elixir, rather than editing them here. That way you don't need to
-- change them again when you update.
--
-- Documentation for each option can be found in the API section of the README.
local defaults = {
  source    = "source",
  build     = "build",
  fileName  = "elixir",
  fileExt   = ".rbxmx",
  rbxName   = "Elixir",
  rbxClass  = "Folder",
  ignored   = nil,
  engine    = nil
}

--------------------------------------------------------------------------------
-- Utility
--------------------------------------------------------------------------------

local function isDirectory(path)
  return lfs.attributes(path, "mode") == "directory"
end

local function splitFileName(file)
  -- Server.Main.lua -> Server.Main, lua
  return file:match("(.+)%.(.+)$")
end

local function getFileContents(path)
  local file = assert(io.open(path))
  local content = file:read("*a")
  file:close()
  return content
end

local function saveToFile(path, content)
  local file = assert(io.open(path, "w"))
  file:write(content)
  file:flush()
  file:close()
end

-- Used to add extra options supplied by the user to the 'defaults' table.
--
-- base - The Table to overwrite
-- ext  - The Table whose keys will overwrite matching keys in 'base'
--
-- Returns 'base' with keys added from 'ext'
local function extend(base, ext)
  if not ext then return base end
  for k,v in pairs(ext) do
    base[k] = v
  end
  return base
end

-- This function allows you to embed ROBLOX properties at the top of a file
-- using inline comments.
--
-- View the "Script Properties" section of the README to learn more.
--
-- path - The path to the file to read for embedded properties.
--
-- Returns a table containing key/value pairs of the embedded properties.
local function getEmbeddedProperties(path)
  local properties = {}
  -- Currently this will only find embedded properties if they are not preceded
  -- by whitespace. Having a single newline at the start of the file prevents
  -- the properties from being found.
  local pattern = "^%-+ (.*): (.*)" -- "-- ClassName: Script"

  for line in io.lines(path) do
    local key, value = line:match(pattern)
    if key and value then
      properties[key] = value
    else
      break
    end
  end

  return properties
end

local function getScriptProperties(path, file)
  local properties = getEmbeddedProperties(path)
  local defaultProperties = {
    Name = file,
    ClassName = "Script",
    Source = getFileContents(path)
  }
  return extend(defaultProperties, properties)
end

--------------------------------------------------------------------------------
-- ROBLOX Model Builder
--------------------------------------------------------------------------------

local model = {
  referent = 0
}

-- The "referent" attribute is applied to every <Item> tag, and is used as a
-- unique identifier for each instance in the game.
function model.ref()
  model.referent = model.referent + 1
  return model.referent
end

-- Checks Lua code for syntax errors.
--
-- Everything will be compiled regardless, but if there are errors you will be
-- notified in the console.
--
-- This is purely for syntax errors. ROBLOX globals like 'game' and 'workspace'
-- are ignored.
--
-- source - The String to check for syntax errors. Typically the entire contents
--          of a Lua file.
function model.lintScript(source)
  local func, err = loadstring(source, "")
  if not func then
    print("WARNING: "..err:gsub("^%[.-%]:", "line "))
  end
end

local function encodeProperty(property, value)
  local stringTag = "<string name=\"%s\">%s</string>"
  local boolTag = "<bool name=\"%s\">%s</bool>"
  -- Lua code is wrapped in a CDATA tag. No need to escape characters.
  local codeTag = "<ProtectedString name=\"%s\"><![CDATA[%s]]></ProtectedString>"

  if type(value) == "string" then
    if property == "Source" then
      return codeTag:format(property, value)
    else
      return stringTag:format(property, value)
    end
  elseif type(value) == "boolean" then
    return boolTag:format(property, tostring(value))
  end
end

function model.properties(propertyList)
  local propertiesTag = "<Properties>%s</Properties>"

  local propertyTags = {}
  for property, value in pairs(propertyList) do
    if property ~= "ClassName" then
      table.insert(propertyTags, encodeProperty(property, value))
    end
  end

  return propertiesTag:format(table.concat(propertyTags))
end

function model.item(itemType, propertyList)
  local className = propertyList.ClassName
  local referentId = model.ref()
  local properties = model.properties(propertyList)

  local itemTag = "<Item class=\"%s\" referent=\"RBX%s\">%s</Item>"

  if itemType == "folder" then
    itemTag = "<Item class=\"%s\" referent=\"RBX%s\">%s"
  end

  return itemTag:format(className, referentId, properties)
end

--------------------------------------------------------------------------------
-- Compiler
--------------------------------------------------------------------------------

local Compiler = {}

function Compiler.new(obj)
  obj = obj or {}
  return setmetatable(obj, { __index = Compiler })
end

function Compiler:ConstructRobloxHierarchy()
  local hierarchy = {}

  local function recurse(path)
    for file in lfs.dir(path) do
      if file ~= "." and file ~= ".." then
        local fullPath = path.."/"..file

        print(fullPath)

        if isDirectory(fullPath) then
          local properties = { Name = file, ClassName = self.rbxClass }
          table.insert(hierarchy, model.item("folder", properties))
          recurse(fullPath)
          table.insert(hierarchy, "</Item>")
        else
          local properties = getScriptProperties(fullPath, file)
          model.lintScript(properties.Source)
          table.insert(hierarchy, model.item("script", properties))
        end
      end
    end
  end
  recurse(self.source)

  return table.concat(hierarchy)
end

--------------------------------------------------------------------------------
-- Elixir
--------------------------------------------------------------------------------

function elixir.compile(options)
  options = extend(defaults, options)

  local compiler = Compiler.new(options)
  local robloxTag = "<roblox xmlns:xmime=\"http://www.w3.org/2005/05/xmlmime\" "..
    "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "..
    "xsi:noNamespaceSchemaLocation=\"http://www.roblox.com/roblox.xsd\" "..
    "version=\"4\">%s</roblox>"
  local body = compiler:ConstructRobloxHierarchy()
  local modelFile = robloxTag:format(body)

  local dest = options.build.."/"..options.fileName..options.fileExt

  lfs.mkdir(options.build)
  saveToFile(dest, modelFile)
  print("\nCompiled to: "..dest)
end

setmetatable(elixir, {
  __call = function(_, ...)
    return elixir.compile(...)
  end
})

return elixir
