## Using Processors

This is an example project that shows you how to use alternative processors when
compiling.

Peruse `elixir.processors` to see the available processor classes. From there
you can pick the one you want and import it. Then you pass it as the `processor`
argument to the compiler.

```python
from elixir.compiler import ModelCompiler
from elixir.processors import NevermoreProcessor

source = "src/"
dest = "model.rbxmx"

compiler = ModelCompiler(source, dest, processor=NevermoreProcessor)
compiler.compile()
```

This example is using Nevermore and its processor. If you're creating a
Nevermore project, remember to grab the latest version from
[Quenty/NevermoreEngine](https://github.com/Quenty/NevermoreEngine/). The ones
provided in the example could become outdated, don't rely on them for your game.
