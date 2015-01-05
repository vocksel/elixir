# Elixir

Elixir is a compiler for use with ROBLOX projects. You supply it with a directory, and it will convert all sub-directories and Lua files into a ROBLOX-compatible XML object that you can import into your game.

Elixir works best for someone that likes to work outside of ROBLOX Studio, where you can use your favorite text editor and VCS to develop your games. Native support for the [Nevermore](https://github.com/Quenty/NevermoreEngine) engine is also included, to make game development even more of a breeze.

Originally adapted from the build system used in [Cure](https://github.com/Anaminus/roblox-cure). Without it I wouldn't have known something like this was possible.

## Getting Started

You'll need a Lua interpreter and the LuaFileSystem module installed to run this file. In Windows this can be done by installing [LuaForWindows]( https://code.google.com/p/luaforwindows/), which comes bundled with LuaFileSystem.

Once you have Lua installed, all you have to do is get a copy of Elixir and call it.

```lua
local elixir = require "elixir"

elixir()
```

It's that easy. Now you can run `lua build.lua` from the command line and all your source code will be compiled into a ROBLOX model file.

Read on to learn how to set ROBLOX properties for your Scripts, and the different options you can configure when calling Elixir.

## Script Properties

When working with Elixir, there is no Properties panel like you would find in Studio to distinguish Scripts, ModuleScripts and LocalScripts. Instead, we have to use other methods of deriving the properties.

### Filename Properties

ROBLOX properties for each Script are derived from the filename. `HelloWorld.local.lua` creates a LocalScript named HelloWorld, `Rainbow.module.lua` creates a ModuleScript named Rainbow, and so on.

`filename.classname.lua` is the format, and these are the supported classes:

- `local`
- `module`

Anything else is compiled to a Script. While not necessary, you can name your files `Something.script.lua` for consistency.

### Embedded Properties

Another way to set properties for a Script is by embedding them in comments at the top of the file. If we had a file named `boring-script.module.lua` with the following contents:

```lua
-- Name: SomeCoolScript
-- ClassName: LocalScript

[code]
```

Then a LocalScript named SomeCoolScript would be created. Embedding the properties keeps filenames concise while still giving the desired outcome when compiling.

**Note:** Embedded properties take precedence over filename properties.

## API

### elixir([options])

```lua
-- No options. Uses defaults
elixir()

-- Uses different 'source' and 'build' directories
elixir{
  source = "src",
  build = "dist"
}
```

#### options

- Type: `Table`

All configurable values for Elixir can be modified in this table.

**Note:** the locations for `options.source` and `options.build` are relative to where you call Elixir from. If you have Elixir under `project/lib/elixir`, and your build file under `project/build.lua`, then when you run the build script it will find the source folder under `project/source`.

#### options.source

- Type: `String`
- Default: `source`

Name of the directory that holds your source code, relative to where you call Elixir from. Automatically generated when Elixir is run, but you'll likely want to create it yourself.

#### options.build

- Type: `String`
- Default: `build`

Name of the directory where the model file is output. Automatically generated when Elixir is run.

#### options.fileName

- Type: `String`
- Default: `elixir`

Name of the file created in `options.build`. This can be anything you like, it's only the name of the file on your system. `options.modelName` controls the in-game name.

#### options.fileExt

- Type: `String`
- Default: `.rbxmx`

ROBLOX recognizes `rbxm` and `rbxmx` as Model files that you can drag-and-drop into Studio. `rbxm` uses Binary, while `rbxmx` uses XML. Because Elixir only compiles to XML, the `rbxmx` extension is prefered.

#### options.rbxName

- Type: `String`
- Default: `Elixir`

Name of the top-most instance in the model file (the root). This contains all of the descendants of the compiled source directory.

#### options.rbxClass

- Type: `String`
- Default: `Configuration`

The ROBLOX instance that will be used to replicate the folder structure. Any instance can be used, but Configurations are recommended.

#### options.engine

- Type: `String`

Engines, in the context of Elixir, are frameworks you can use to assist with developing your games. They come with their own code and require a specific directory structure to work correctly, but with the added benefit of handling run-time tasks.

Note that engines have the possibility to override the options you can configure. For example, Nevermore needs `rbxName` set to `Nevermore` to run. Any changes you make to that option will have no effect.

```lua
elixir{
  engine = "Nevermore",
  rbxName = "Project" -- Overridden by Nevermore.
}
```


Applicable engines:

- `Nevermore` (https://github.com/Quenty/NevermoreEngine)

  - Overrides the `rbxName` option, setting it to `Nevermore`. Nevermore uses `ServerScriptService.Nevermore` when referencing itself.
  - `NevermoreEngineLoader.lua` is compiled to a Script, and will not be disabled. This is the only script that should be enabled in the game.
  - All Scripts and LocalScripts will be disabled.
  - All other Lua files will be compiled into ModuleScripts.

  Copy the `App` and `Modules` directories from Nevermore into the source folder, deleting any of the modules that you don't require. Create `Modules/Game` and two files inside that, `Server.Main.lua` and `Client.Main.lua`. The directory structure should look like this:

  ```
  source/
    App/
      NevermoreEngine.lua
      NevermoreEngineLoader.lua
    Modules/
      Game/
        Client.Main.lua
        Server.Main.lua
      ...
  ```

  Inside of the new 'Main' files, you need to add the following comments to the top of them:

  *Server.Main.lua:*

  ```lua
  -- Name: Server.Main
  -- ClassName: Script

  [code]
  ```

  *Client.Main.lua:*

  ```lua
  -- Name: Client.Main
  -- ClassName: LocalScript

  [code]
  ```

  Because everything is compiled to a module (save for `NevermoreEngineLoader.lua`), you need to override that by setting the ClassName manually.

#### options.ignored

- Type: `Array`

Files to skip over when compiling. Especially useful when using .gitignore to commit empty directories.
