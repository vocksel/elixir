import re
from xml.etree import ElementTree

"""Functions for creating ROBLOX instances in XML"""

def _is_lua_comment(line):
    """Checks if `line` is a Lua comment.

    line : str
        A line from some Lua source code.
    """

    # Matching spaces so that we don't pick up block comments (--[[ ]])
    return re.match(r"^--\s+", line)

def _convert_bool(b):
    """Converts Python bool values to Lua's.

    Before we can insert a bool value in the XML, it must first be converted to
    a string and then lowercased to match Lua's bool values.
    """
    return str(b).lower()

def _sanitize(content):
    """Makes sure `content` is safe to go in the XML.

    This is mostly for converting Python types into something XML compatible.
    """

    if type(content) == bool:
        return _convert_bool(content)
    else:
        return content

def is_module(content):
    """Checks if the contents are from a Lua module.

    It looks for a returned value at the end of the file. If it finds one, it's
    safe to assume that it's a module.

    content : str
        The Lua source code to check.
    """

    # We match any number of whitespace after the return in case of accidental
    # spacing on the user's part. Then we match any characters to catch both
    # variables (`return module`) and functions (`return setmetatable(t1, t2)`)
    #
    # We're optionally matching any number of spaces at the end of the file
    # incase of a final newline, or accidentally added spaces after the value.
    return re.search(r"return\s+.*(\s+)?$", content)

def tostring(element):
    """A more specialized version of ElementTree's `tostring`.

    We're using Unicode encoding so that this returns a string, instead of the
    default bytestring.

    We're also setting `short_empty_elements` to `False` so that all elements
    are output with their ending tags. This is only required when _writing_ the
    XML, as ROBLOX won't import the file if there are any self-closing tags.

    This isn't used for writing, so while this isn't mandatory, it's done here
    so the string version of the XML is consistent with what gets written.
    """

    return ElementTree.tostring(element, encoding="unicode",
        short_empty_elements=False)

class PropertyElement:
    """Container for the properties of InstanceElement.

    This stores things like the Instance's in-game name, and for Scripts it can
    hold the source code, as well as if the Script is disabled or not.
    """

    def __init__(self, parent):
        self.element = ElementTree.SubElement(parent, "Properties")

    def add(self, tag, name, text):
        """Add a new property.

        tag : str
            The type of property. This will typically be "string", "bool" or
            "ProtectedString".
        name : str
            The property's name. For example, you would use a tag of "bool" and
            a name of "Disabled" for the Disabled property of a Script.
        """

        prop = ElementTree.SubElement(self.element, tag, name=name)
        prop.text = _sanitize(text)

        return prop

    def get(self, name):
        return self.element.find("*[@name='{}']".format(name))

    def set(self, name, newValue):
        prop = self.get(name)
        if prop is not None:
            prop.text = newValue

class InstanceElement:
    """Acts as an XML implementation of ROBLOX's Instance class.

    This class is intended to be very barebones, you will typically only use it
    for Folder instances. Other classes like ScriptElement are created to extend
    its functionality.

    class_name : str
        This can be any ROBLOX class.
        http://wiki.roblox.com/index.php?title=API:Class_reference
    name=None : str
        The name of the instance in-game. This will default to `class_name`.
    """

    def __init__(self, class_name, name=None):
        name = name or class_name

        # `class` is a reserved keyword so we have to pass it in through
        # `attrib` rather than as a named parameter.
        self.element = ElementTree.Element("Item", attrib={"class": class_name})

        self.properties = PropertyElement(self.element)
        self.name = self.properties.add("string", "Name", name)

class ScriptElement(InstanceElement):
    def __init__(self, class_name="Script", name=None, source=None,
        disabled=False):
        super().__init__(class_name, name)

        self.source = self.properties.add("ProtectedString", "Source", source)
        self.disabled = self.properties.add("bool", "Disabled", disabled)

    def get_first_comment(self):
        """Gets the first comment in the source.

        This only applie to the first _inline_ comment (the ones started with
        two dashes), block comments are not picked up.

        This is used by get_embedded_properties() to parse the comment for
        properties to override the defaults.
        """

        source = self.source.text

        if not source: return

        found_first_comment = False
        comment_lines = []

        for line in source.splitlines():
            is_comment = _is_lua_comment(line)
            if is_comment:
                found_first_comment = True
                comment_lines.append(line)

            # The first comment ended, time to break out
            elif not is_comment and found_first_comment:
                break

        if comment_lines:
            return "\n".join(comment_lines)

    def get_embedded_properties(self):
        """Gets properties that are embedded in the source.

        When working on the filesystem, there is no Properties panel like you
        would find in ROBLOX Studio. To make up for this, properties can be
        defined using inline comments at the top of your Lua files.

        If this instance had the following source:

            -- Name: HelloWorld
            -- ClassName: LocalScript

            local function hello()
              return "Hello, World!"
            end

        Running this method will return a dict of:

            { "Name": "HelloWorld", "ClassName": "LocalScript" }
        """

        comment = self.get_first_comment()

        # If there's no comment then there won't be any embedded properties. No
        # need to continue from here.
        if not comment: return

        # For `name` we only need to match whole words, as ROBLOX's
        # properties don't have any special characters. `value` on the other
        # hand can use any character.
        property_pattern = re.compile(r"(?P<name>\w+):\s+(?P<value>.+)")

        property_list = {}

        for match in property_pattern.finditer(comment):
            property_list[match.group("name")] = match.group("value")

        return property_list

    def use_embedded_properties(self):
        """Overrides the current properties with any embedded ones."""

        properties = self.get_embedded_properties()

        if not properties: return

        for prop_name, prop_value in properties.items():
            if prop_name == "ClassName":
                self.element.set("class", prop_value)
            else:
                self.properties.set(prop_name, prop_value)

class ContainerElement(InstanceElement):
    def __init__(self, class_name="Folder", name=None):
        super().__init__(class_name, name)

class ModelElement:
    def __init__(self, content):
        self.element = ElementTree.XML(content)
