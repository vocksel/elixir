# Elixir

Adapted from the build system used in [Cure](https://github.com/Anaminus/roblox-cure), Elixir builds a directory structure and Lua files into a ROBLOX compatible XML file. Write your code, compile it, and drag-and-drop the generated file into your game.

ROBLOX currently has no Git integration, and minimal theming options. With Elixir you can use your favorite version control system and text editor.

## Getting Started

You'll need a Lua interpreter and the LuaFileSystem module installed to run this file. In Windows this can be done by installing [LuaForWindows]( https://code.google.com/p/luaforwindows/), which comes bundled with LuaFileSystem.

Once you have Lua installed, all you have to do is get a copy of Elixir and call it.

```lua
-- build.lua

local elixir = require "lib/elixir"

elixir()
```

It's that easy. Now you can run `lua build.lua` from the command line and all your source code will be compiled into a ROBLOX model file.
