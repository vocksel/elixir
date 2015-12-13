import os
import os.path
from xml.etree import ElementTree

from elixir.rbx import Container
from elixir.processors import BaseProcessor

def create_path(path):
    parent_folders = os.path.dirname(path)
    if parent_folders and not os.path.exists(parent_folders):
        os.makedirs(parent_folders)

class BaseCompiler:
    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

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
    model_name=None : str
        This is the name of the top-most folder that contains all of your source
        code.

        If blank, it will use the name of the last folder in `source`. This
        default isn't always desired. For example, if all of your code is under
        `src/`, you might not want that to be the name of your project in-game.
    processor=None : BaseProcessor
        The processor to use when compiling.

        A processor is what handles files and folders as the compiler comes
        across them. It dictates the type of ROBLOX class is returned.

        For example, when BaseProcessor comes across a Lua file, it will return
        a new `elixir.rbx.Script` instance.
    """

    def __init__(self, source, dest, model_name=None, processor=None):
        super().__init__(source, dest)

        if model_name is None:
            model_name = os.path.basename(source)

        if processor is None:
            processor = BaseProcessor

        self.processor = processor(model_name)

    def _get_base_tag(self):
        """Gets the base <roblox> tag that emcompasses the model.

        This should always be the first element in the file. All others are
        appended to this tag.
        """

        return ElementTree.Element("roblox", attrib={
            "xmlns:xmine": "http://www.w3.org/2005/05/xmlmime",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi": "http://www.roblox.com/roblox.xsd",
            "version": "4" })

    def _get_element(self, path):
        if os.path.isdir(path):
            return self.processor.process_folder(path)
        elif os.path.isfile(path):
            return self.processor.process_script(path)

    def _create_hierarchy(self, path):
        """Turns a directory structure into ROBLOX-compatible XML.

        path : str
            The path to a directory to recurse through.
        """

        # This is the folder that holds all the source code.
        root = self.processor.get_base_container()
        root_xml = root.get_xml()

        def recurse(path, hierarchy):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)

                element = self._get_element(item_path)
                element_xml = element.get_xml()

                hierarchy.append(element_xml)

                if os.path.isdir(item_path):
                    recurse(item_path, element_xml)

        recurse(path, root_xml)

        return root_xml

    def _create_model(self):
        model = self._get_base_tag()
        hierarchy = self._create_hierarchy(self.source)
        model.append(hierarchy)

        return model

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
