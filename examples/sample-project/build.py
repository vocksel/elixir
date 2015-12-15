import os.path

from elixir.compiler import ModelCompiler

source = "src/"
dest = "model.rbxmx"

compiler = ModelCompiler(source, dest)
compiler.compile()
