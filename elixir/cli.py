import os
import argparse

from elixir.compiler import ModelCompiler

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="The directory whose contents will be "
        "compiled into a ROBLOX model file")
    parser.add_argument("-d", "--dest",
        help="Where the compiled source will be output to. Directories in this "
             "path will be created for you. The extension is set by the "
             "\"--extension\" argument. (default: \"elixir\")")
    parser.add_argument("-x", "--extension", default=".rbxmx",
        help="")
    parser.add_argument("-n", "--rbx_name",
        help="The name of the top-level container folder (default: name of "
        "`source` argument)")
    parser.add_argument("-c", "--rbx_class", default="Folder",
        help="The ROBLOX instance used as a container (default: \"Folder\")")
    parser.add_argument("-e", "--engine", choices=["nevermore"],
        help="Use an engine when compiling")

    return parser.parse_args()

def compile_model(source, dest):
    root = os.getcwd()
    source = os.path.join(root, source)

    try:
        dest = os.path.join(root, dest)
        ModelCompiler(source, dest).compile()
    except TypeError:
        # This is only if there's no `dest`. I probably shouldn't be doing
        # things this way.
        ModelCompiler(source).compile()

def main():
    args = parse_arguments()
    compile_model(args.source, args.dest)

if __name__ == '__main__':
    main()
