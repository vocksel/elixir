"""Elixir

Usage:
  elixir <source> <dest> [options]
  elixir -h | --help

Options:
    -h, --help              Show this screen.
    -m, --model-name <name> The name of the top-level container folder (default:
                            folder name of the `source` argument.)
    -p, --processor <name>  Use an engine when compiling.
"""

import os
import os.path

from docopt import docopt

from elixir.compilers import ModelCompiler
import elixir.processors

def get_processor(processor_name):
    """Gets a processor by its name.

    This allows the user to reference one of the processors from the command
    line. Since you can't directly get the class itself from a command, we need
    to use a string.

    processor_name : str
        The name of one of the available processors.
    """

    if processor_name in dir(elixir.processors):
        return getattr(elixir.processors, processor_name)
    else:
        return elixir.processors.BaseProcessor

def main():
    args = docopt(__doc__)

    source = os.path.abspath(args["<source>"])
    dest = os.path.abspath(args["<dest>"])
    model_name = args["--model-name"]
    processor = args["--processor"] or "BaseProcessor"

    compiler = ModelCompiler(source, dest, model_name=model_name,
        processor=get_processor(processor))
    compiler.compile()

if __name__ == '__main__':
    main()
