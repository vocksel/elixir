import os.path

from elixir.compiler import ModelCompiler

source = "src/"
dest = "model.rbxmx"
model_name = "SampleProject"

compiler = ModelCompiler(source, dest, model_name=model_name)
compiler.compile()
