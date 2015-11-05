import os
import os.path
from xml.etree import ElementTree

from elixir.rbx import Container, Script

class ModelCompiler:
    """Compiles a ROBLOX-compatible XML file.

    It takes directories and certain files under them and turns them into an
    ROBLOX model file. ROBLOX recognizes these files and allows you to
    drag-and-drop them right into your game.

    Usage:

        # Getting paths to the source and dest directories
        root = os.path.abspath(os.path.dirname(__file__))
        source = os.path.join(root, "source")
        build = os.path.join(root, "build")

        # Compiles everything under `source` as a model file to `build`.
        model = ModelCompiler(source, build)
        model.compile()

    source : str
        The directory containing Lua code and ROBLOX Models that you want Elixir
        to compile.
    dest="elixir" : str
        The name of the file that will be created when compiling. Directories in
        this path are automatically created for you.
    extension=".rbxmx" : str
        The extension appended to `dest`. It is important that this value be
        either `.rbxmx` or `.rbxm`, as those are the two extensions ROBLOX
        recognizes as Model files.

        You won't be able to import the file otherwise.
    """

    def __init__(self, source, dest="elixir", extension=".rbxmx"):
        self._make_dirs(dest)

        self.source = source
        self.dest = dest+extension

    def _make_dirs(self, path):
        parent_folders = os.path.dirname(path)
        if parent_folders and not os.path.exists(parent_folders):
            os.makedirs(parent_folders)

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
            return Container(path)
        elif os.path.isfile(path):
            return Script(path)

    def _construct_hierarchy(self, path):
        """Turns a directory structure into ROBLOX-compatible XML.

        path : str
            The path to a directory to recurse through.
        """

        hierarchy = Container(path).get_xml()

        def recurse(path, parent=hierarchy):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                element = self._get_element(item_path).get_xml()
                parent.append(element)

                if os.path.isdir(item_path):
                    recurse(item_path, parent=element)
        recurse(path)

        return hierarchy

    def _get_model_content(self):
        model = self._get_base_tag()
        hierarchy = self._construct_hierarchy(self.source)
        model.append(hierarchy)

        return model

    def compile(self):
        """Compiles source code into a ROBLOX Model file."""

        # Writing as binary so that we can use UTF-8 encoding.
        with open(self.dest, "wb+") as f:
            content = self._get_model_content()
            tree = ElementTree.ElementTree(content)

            # ROBLOX does not support self-closing tags. In the event that an
            # element is blank (eg. a script doesn't have any contents) you
            # won't be able to import the model. We need to ensure all elements
            # have an ending tag by setting `short_empty_elements=False`.
            tree.write(f, encoding="utf-8", short_empty_elements=False)
