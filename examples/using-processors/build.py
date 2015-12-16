from elixir.compilers import ModelCompiler
from elixir.processors import NevermoreProcessor

source = "src/"
dest = "model.rbxmx"

compiler = ModelCompiler(source, dest, processor=NevermoreProcessor)
compiler.compile()
