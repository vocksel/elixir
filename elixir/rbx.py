import os.path
import re
from xml.etree import ElementTree

import elixir.fs
from elixir.rbxxml import new_property, create_instance_xml, create_script_xml

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

class Instance:
    def __init__(self, class_name, name=None):
        # ROBLOX uses the class of the instance for its name so we're doing the
        # same here.
        name = name or class_name

        xml, xml_properties = create_instance_xml(class_name, name)

        self.class_name = class_name
        self.name = name
        self.xml = xml
        self.xml_properties = xml_properties

    def get_xml(self):
        """Gets the instance's XML for the ROBLOX model.

        This is for backwards compatibility. You should use the `xml` property
        in new code.
        """
        return self.xml

class Container(Instance):
    """A class to represent filesystem directories in-game.

    name=None : str
        The name of the Container in-game.
    """

    def __init__(self, name=None):
        super().__init__("Folder", name)

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
        self.disabled = disabled

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

        return create_script_xml(self.class_name, self.name, self.source,
            self.disabled)
