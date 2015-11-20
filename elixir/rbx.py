import re
from xml.etree import ElementTree

import elixir.fs

class Referent:
    """Gets a unique ID for a ROBLOX instance.

    The "referent" attribute is applied to every <Item> tag, and is used to make
    each instance unique.
    """
    def __init__(self):
        self.counter = 0

    def increment(self):
        self.counter += 1
        return "RBX{}".format(self.counter)

ref = Referent()

def create_item(class_name):
    item = ElementTree.Element("Item", attrib={
        "class": class_name,
        "referent": ref.increment() })

    # Add an empty list of properties to fill later.
    ElementTree.SubElement(item, "Properties")

    return item

class Container(elixir.fs.Folder):
    """Acts as a directory in the ROBLOX hierarchy.

    path : str
        The path to a directory on the filesystem.
    class_name : str
        This is the name of a ROBLOX class that will be used to contain scripts
        and models. This can be any one of ROBLOX's classes, but it's
        recommended to use a Folder.
    """

    def __init__(self, path, class_name="Folder"):
        super().__init__(path)
        self.class_name = class_name

    def get_xml(self):
        """Gets the Container as XML in a ROBLOX-compatible format."""

        item = create_item(self.class_name)
        properties = item.find("Properties")
        name = ElementTree.SubElement(properties, "string", name="Name")
        name.text = self.name

        return item

class Model(elixir.fs.File):
    """A ROBLOX Model file.

    Any file with an `rbxmx` extension is a ROBLOX Model. They are XML files
    containing the data of an in-game model.

    Typically this is used to import existing models when compiling.

    path : str
        The path to a .rbxmx file.
    """

    def __init__(self, path):
        super().__init__(path)

    def get_importable_contents(self):
        """Gets the Model's contents.

        This allows existing ROBLOX Models to be imported into the output file
        when compiling.
        """

        content = self.read()
        return re.sub(r"</?roblox.*>", "", content)

class Script(elixir.fs.File):
    """A representation of a ROBLOX Script.

    path : str
        The path to a .lua file.
    """

    def __init__(self, path):
        super().__init__(path)

        properties = self._get_properties()

        self.name = properties["Name"]
        self.class_name = properties["ClassName"]
        self.source = self.read()

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
        property_pattern = re.compile(r"(?P<name>\w+):\s+(?P<value>.+)")
        property_list = {}
        if comment:
            for match in property_pattern.finditer(comment):
                property_list[match.group("name")] = match.group("value")
        return property_list

    def _get_properties(self):
        """Extracts ROBLOX properties.

        Things like the `Name` and `ClassName` properties that ROBLOX uses. This
        method retrieves them by using aspects of the Script.
        """

        defaults = { "Name": self.name, "ClassName": "Script" }
        properties = self._get_embedded_properties()
        defaults.update(properties)
        return defaults

    def get_xml(self):
        """Gets the Script as XML in a ROBLOX-compatible format."""

        item = create_item(self.class_name)
        properties = item.find("Properties")

        name = ElementTree.SubElement(properties, "string", name="Name")
        name.text = self.name

        source = ElementTree.SubElement(properties, "ProtectedString",
            name="Source")
        source.text = self.source

        return item
