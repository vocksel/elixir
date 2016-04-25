import os.path
import re
from xml.etree import ElementTree

import elixir.fs

def is_module(path):
    """Checks if the file is a Lua module.

    path : str
        The path to a Lua file.
    """

    with open(path) as f:
        content = f.read()

    # Looks for a returned value at the end of the file. If it finds one, it's
    # safe to assume that we're looking at a Lua module.
    #
    # We match any number of whitespace after the return in case of accidental
    # spacing on the user's part. Then we match any characters to catch both
    # variables (`return module`) and functions (`return setmetatable(t1, t2)`)
    #
    # We're optionally matching any number of spaces at the end of the file
    # incase of a final newline, or accidentally added spaces after the value.
    return re.search(r"return\s+.*(\s+)?$", content)

def create_item(class_name):
    # A "referent" used to be applied as an attribute, but it is no longer
    # needed. A referent is a sort of ID for each ROBLOX instance in the XML.
    # ROBLOX imports models just fine without them, so it's not necessary to
    # include.
    item = ElementTree.Element("Item", attrib={
        # `class` is a reserved keyword so we have to pass it in through this
        # dict rather than as a named parameter.
        "class": class_name
    })

    # Add an empty list of properties to fill later.
    ElementTree.SubElement(item, "Properties")

    return item

class Container:
    """Acts as a directory in the ROBLOX hierarchy.

    name="Folder" : str
        The name of the container in the ROBLOX hierarchy.
    class_name="Folder" : str
        This is the name of a ROBLOX class that will be used to contain scripts
        and models. This can be any one of ROBLOX's classes, but it's
        recommended to use a Folder.
    """

    def __init__(self, name="Folder", class_name="Folder"):
        self.name = name
        self.class_name = class_name

    def get_xml(self):
        """Gets the Container as XML in a ROBLOX-compatible format."""

        item = create_item(self.class_name)
        properties = item.find("Properties")

        name = ElementTree.SubElement(properties, "string", name="Name")
        name.text = self.name

        return item

class Model:
    """A ROBLOX Model file.

    Any file with an `rbxmx` extension is a ROBLOX Model. They are XML files
    containing the data of an in-game model.

    Typically this is used to import existing models when compiling.

    path : str
        The path to a .rbxmx file.
    """

    def __init__(self, path):
        self.path = path

    def get_xml(self):
        """Get's the Model's XML.

        This is used to import existing models into the model currently being
        compiled.
        """

        tree = ElementTree.parse(self.path)
        root = tree.getroot()

        return root

class Script(elixir.fs.File):
    """A representation of a ROBLOX Script.

    path : str
        The path to a .lua file.
    class_name="Script" : str
        The type of Script you want to create.

        As of writing this, "Script", "LocalScript" and "ModuleScript" are the
        three main types of Scripts.
    disabled=False : bool
        Whether the Script will be disabled in-game. A disabled script will not
        run when the game starts.
    """

    def __init__(self, path, class_name="Script", disabled=False):
        super().__init__(path)

        properties = self._get_embedded_properties()

        filename = os.path.basename(path)
        name = os.path.splitext(filename)[0]

        self.name = properties.get("Name") or name
        self.class_name = properties.get("ClassName") or class_name
        self.source = self.read()

        # This needs to be converted to a string so that it can be written as
        # XML.
        #
        # Also, ROBLOX's bool values are `true` and `false`, so it needs to be
        # lowercased.
        self.disabled = str(disabled).lower()

    def _get_first_comment(self):
        """Gets the first comment in a Lua file.

        This only applie to the first _inline_ comment (the ones started with
        two dashes), block comments are not picked up.
        """

        # Matching spaces so that we don't pick up block comments (--[[ ]])
        comment_pattern = re.compile(r"^--\s+")

        found_first_comment = False
        comment_lines = []

        with open(self.path) as f:
            for line in f:
                is_comment = comment_pattern.match(line)
                if is_comment:
                    found_first_comment = True
                    comment_lines.append(line)
                elif not is_comment and found_first_comment:
                    return "".join(comment_lines)

    def _get_embedded_properties(self):
        """Gets the embedded properties in a Lua script.

        When working with Elixir, there is no Properties panel like you would
        find in ROBLOX Studio. To make up for this, properties are defined using
        inline comments at the top of your Lua files.

        Given a script with the following contents:

            -- Name: HelloWorld
            -- ClassName: LocalScript

            local function hello()
              return "Hello, World!"
            end

        Running this method on it will return a dict of:

            { "Name": "HelloWorld", "ClassName": "LocalScript" }
        """

        comment = self._get_first_comment()

        # Matches "-- Name: Value"
        property_pattern = re.compile(r"(?P<name>\w+):\s+(?P<value>.+)")
        property_list = {}

        if comment:
            for match in property_pattern.finditer(comment):
                name = match.group("name")
                value = match.group("value")
                property_list[name] = value

        return property_list

    def get_xml(self):
        """Gets the Script as XML in a ROBLOX-compatible format."""

        item = create_item(self.class_name)
        properties = item.find("Properties")

        name = ElementTree.SubElement(properties, "string", name="Name")
        name.text = self.name

        disabled = ElementTree.SubElement(properties, "bool", name="Disabled")
        disabled.text = self.disabled

        source = ElementTree.SubElement(properties, "ProtectedString",
            name="Source")
        source.text = self.source

        return item
