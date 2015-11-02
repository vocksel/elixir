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

    # Add empty properties to propagate later.
    ElementTree.SubElement(item, "Properties")

    return item

class Script(elixir.fs.File):
    def __init__(self, path):
        super().__init__(path)

        properties = self._get_properties()

        self.name = properties["Name"]
        self.class_name = properties["ClassName"]
        self.source = self._get_source()

    def _get_source(self):
        with open(self.path) as f:
            return f.read()

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
        defaults = { "Name": "Script", "ClassName": "Script" }
        properties = self._get_embedded_properties()
        defaults.update(properties)
        return defaults

    def get_xml(self):
        """Gets the script as XML in a ROBLOX-compatible format."""

        item = create_item(self.class_name)
        properties = item.find("Properties")

        name = ElementTree.SubElement(properties, "string", name="Name")
        name.text = self.name

        source = ElementTree.SubElement(properties, "ProtectedString",
            name="Source")
        source.text = self.source

        return item
