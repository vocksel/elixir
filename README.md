# Elixir

Adapted from the build system used in [Cure](https://github.com/Anaminus/roblox-cure), Elixir builds a directory structure and Lua files into a ROBLOX compatible XML file. Write your code, compile it, and drag-and-drop the generated file into your game.

ROBLOX currently has no Git integration, and minimal theming options. With Elixir you can use your favorite version control system and text editor.

## Setup

You'll need a Lua interpreter and the LuaFileSystem module installed to run this file. In Windows this can be done by installing [LuaForWindows]( https://code.google.com/p/luaforwindows/), which comes bundled with LuaFileSystem.

From there, you're all set to compile your source code:

```bash
$ lua build.lua
```
