import os
import os.path
from xml.etree import ElementTree

from elixir import rbxmx
from elixir.processors import BaseProcessor

def create_path(path):
    parent_folders = os.path.dirname(path)
    if parent_folders and not os.path.exists(parent_folders):
        os.makedirs(parent_folders)

class BaseCompiler:
    def __init__(self, source, dest):
        self.source = os.path.normpath(source)
        self.dest = os.path.normpath(dest)

    def compile(self):
        create_path(self.dest)

class ModelCompiler(BaseCompiler):
    """Creates a ROBLOX Model from source code.

    It converts folders, Lua files, and ROBLOX models into an XML file that you
    can import into your game.

    Usage:

        # This is just getting paths to the source directory and the file that
        # we'll be outputting to.
        root   = os.path.abspath(os.path.dirname(__file__))
        source = os.path.join(root, "source")
        build  = os.path.join(root, "build/output.rbxmx")

        # Compiles everything under `source/` to `build/output.rbxmx`.
        model = ModelCompiler(source, build)
        model.compile()

    Now you'll have a ROBLOX Model in `build/` that you can drag into your
    ROBLOX level. And just like that, all of your code is there!

    source : str
        The directory containing Lua code and ROBLOX Models that you want
        compiled.
    dest : str
        The name of the file that will be created when compiling. Directories in
        this path are automatically created for you.

        It's important that the file extension should either be `.rbxmx` or
        `.rbxm`. Those are the two filetypes recognized by ROBLOX Studio. You
        won't be able to import the file into your game otherwise.
    processor=None : BaseProcessor
        The processor to use when compiling.

        A processor is what handles files and folders as the compiler comes
        across them. It dictates the type of ROBLOX class is returned.

        For example, when BaseProcessor comes across a Lua file, it will return
        a new `elixir.rbx.Script` instance.
    """

    def __init__(self, source, dest, processor=BaseProcessor):
        super().__init__(source, dest)

        self.processor = processor()

    def _create_hierarchy(self, path):
        """Turns a directory structure into ROBLOX-compatible XML.

        path : str
            The path to a directory to recurse through.
        """

        root_xml = rbxmx.get_base_tag()

        def recurse(path, hierarchy):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)

                element = self.processor.get_element(item_path)
                xml = element.get_xml()
                element.append_to(hierarchy)

                if os.path.isdir(item_path):
                    recurse(item_path, xml)

        recurse(path, root_xml)

        return root_xml

    def _create_model(self):
        return self._create_hierarchy(self.source)

    def _write_model(self):
        """Compiles the model and writes it to the output file."""

        # Writing as binary so that we can use UTF-8 encoding.
        with open(self.dest, "wb+") as f:
            model = self._create_model()
            tree = ElementTree.ElementTree(model)

            # ROBLOX does not support self-closing tags. In the event that an
            # element is blank (eg. a script doesn't have any contents) you
            # won't be able to import the model. We need to ensure all elements
            # have an ending tag by setting `short_empty_elements=False`.
            tree.write(f, encoding="utf-8", short_empty_elements=False)

    def compile(self):
        """Compiles source code into a ROBLOX Model file."""

        super().compile()
        self._write_model()
