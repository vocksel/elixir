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

Read on to learn how to set ROBLOX properties for your Scripts, and the different options you can configure when calling Elixir.

## Script Properties

ROBLOX properties for each Script are derived from the filename. `HelloWorld.local.lua` creates a LocalScript named HelloWorld, `Rainbow.module.lua` creates a ModuleScript named Rainbow, and so on.

`filename.classname.lua` is the format, and these are the supported classes:

- `local`
- `module`

Anything else is compiled to a Script. While not necessary, you can name your files `Something.script.lua` for consistency.

You can also embed the Script's properties at the top of the file in a comment. If we had a file named `boring-script.module.lua` with the following contents:

```lua
-- Name: SomeCoolScript
-- ClassName: LocalScript

[code]
```

Then a LocalScript named SomeCoolScript would be created. Embedding the properties keeps filenames concise while still giving the desired outcome when compiling.

**Note:** Embedded properties take precedence over filename properties.
