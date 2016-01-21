## Module Detection

Elixir will automatically detects if a Lua file is a normal Script or a
ModuleScript, so you don't need to bother with setting properties in most cases.

If you run `python build.py` you can see how `Server.lua` is compiled to a
Script, and `Module.lua` is compiled to a ModuleScript, without explicitly
telling Elixir that.
