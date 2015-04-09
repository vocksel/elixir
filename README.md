# Elixir

Elixir is a compiler for use with ROBLOX projects. You supply it with a
directory, and it will convert all sub-directories and Lua files into a
ROBLOX-compatible XML file that you can import into your game.

Elixir is best for someone that prefers to work outside of ROBLOX Studio,
where you can leverage the full power of Version Control and use your favorite
text editor.

Native support for the [Nevermore][nevermore] engine is also included, to make
game development even more of a breeze.

## Getting Started

You'll need a Lua interpreter and the LuaFileSystem module installed to run
Elixir. In Windows this can be done by installing [LuaForWindows][lfw], which
comes bundled with LuaFileSystem.

Once you have Lua installed, go ahead and grab a copy of Elixir. You can place
it wherever you like, just make sure you can `require()` it.

Next you need to create a file that you will run when you want to compile your
project. `build.lua` is a good name. In the contents of this file paste the
following:

```lua
local elixir = require "elixir"

elixir()
```

Now you can run it with `lua build.lua`, and if you have any Lua files in
`source/`, they should all be compiled to to a ROBLOX model file.

## Properties

When working with Elixir, there is no Properties panel like you would find in
Studio. To make up for this, properties are defined using inline comments at the
top of your Lua files.

```lua
-- Name: HelloWorld
-- ClassName: LocalScript

local function hello()
  return "Hello, World!"
end
```

When compiled, this would create a LocalScript named `HelloWorld`.

List of properties:

- **Name**: Any alphanumeric string can be used for the name (defaults to the
  file name).
- **ClassName**: This can be any one of the Script instances (defaults to
  `Script`).

While you can omit properties when you want to use the defaults, it's advised to
define all of them for consistency.

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

**Note:** the locations for `options.source` and `options.build` are relative
to where you call Elixir from. If you have Elixir under `project/lib/elixir`,
and your build file under `project/build.lua`, then when you run the build
script it will find the source folder under `project/source/`.

#### options.source

- Type: `String`
- Default: `source`

Name of the directory that holds your source code.

#### options.build

- Type: `String`
- Default: `build`

Name of the directory where the model file is output to. Automatically generated
when Elixir is run.

#### options.fileName

- Type: `String`
- Default: `elixir`

Name of the file created in `options.build`. This can be anything you like, it's
only the name of the file on your system. `options.rbxName` controls the in-game
name.

#### options.rbxName

- Type: `String`
- Default: `Elixir`

Name of the top-most instance in the model file (the root). This contains all of
the descendants of the compiled source directory.

#### options.rbxClass

- Type: `String`
- Default: `Folder`

The ROBLOX instance that will be used to replicate the directory structure. Any
instance can be used, but Folders are recommended.

#### options.ignored

- Type: `Array`

A list of files to skip over when compiling. This is especially useful when
using .gitignore, as that's not something normally compiled with your source
code.

#### options.engine

- Type: `String`

Engines are frameworks you can use to assist with developing your games. They
come with their own code and require a specific directory structure to work
correctly, but with the added benefit of making game development significantly
easier.

Engines have the possibility to override the options you can configure. For
example, Nevermore needs `options.rbxName` set to `Nevermore` to run. Any
changes you make to that option will have no effect.

```lua
elixir{
  engine = "Nevermore",
  rbxName = "Project" -- Overridden by Nevermore.
}
```

Applicable engines:

- `Nevermore` (https://github.com/Quenty/NevermoreEngine)

  - Overrides the `rbxName` option, setting it to `Nevermore`. Nevermore
    internally referenced itself as `ServerScriptService.Nevermore`, so it can't
    use the default rbxName of `Elixir`.
  - `NevermoreEngineLoader.lua` is compiled to a Script, and will not be
    disabled. This is the only script that should be enabled in the game.
  - All Scripts and LocalScripts will be disabled.
  - All other Lua files will be compiled into ModuleScripts.

  Copy the `App` and `Modules` directories from Nevermore into the source
  folder, deleting any of the modules that you don't require. Create
  `Modules/Game` and two files inside that, `Server.Main.lua` and
  `Client.Main.lua`. The directory structure should look like this:

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

  Inside of the new 'Main' files, you need to add the following comments to the
  top of them:

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

  Everything is compiled to a module (save for `NevermoreEngineLoader.lua`), so
  you need to override that by setting the ClassName manually.

[nevermore]: https://github.com/Quenty/NevermoreEngine
[lfw]:       https://code.google.com/p/luaforwindows/
