from elixir.compilers import ModelCompiler

source = "src/"
dest = "model.rbxmx"

compiler = ModelCompiler(source, dest)
compiler.compile()
