import os
import os.path
from xml.etree import ElementTree

from elixir.rbx import Container, Script

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
    extension=".rbxmx" : str
        The extension appended to `dest`.

        It's important that this value be either `.rbxmx` or `.rbxm`, as those
        are the two extensions ROBLOX recognizes as Model files. You won't be
        able to import the file otherwise.
    model_name=None : str
        This is the name of the top-most folder that contains all of your source
        code.

        If blank, it will use the name of the last folder in `source`. This
        default isn't always desired. For example, if all of your code is under
        `src/`, you might not want that to be the name of your project in-game.
    """

    def __init__(self, source, dest, extension=".rbxmx", model_name=None):
        super().__init__(source, dest+extension)

        if model_name is None:
            model_name = os.path.basename(source)

        self.model_name = model_name

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

    def _process_dir(self, path):
        filename = os.path.basename(path)
        return Container(filename)

    def _process_file(self, path):
        return Script(path, "Script")

    def _get_element(self, path):
        if os.path.isdir(path):
            return self._process_dir(path)
        elif os.path.isfile(path):
            return self._process_file(path)

    def _create_hierarchy(self, path):
        """Turns a directory structure into ROBLOX-compatible XML.

        path : str
            The path to a directory to recurse through.
        """

        # This is the folder that holds all the source code.
        root = Container(self.model_name)
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
