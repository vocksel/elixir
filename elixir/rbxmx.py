import re
from xml.etree import ElementTree

"""Everything to do with generating ROBLOX instances as XML.

This module is for constructing ROBLOX Models from a folder structure and Lua
files, as well as importing existing Models when compiling.
"""

def _is_lua_comment(line):
    """Checks if a line of text is a Lua comment.

    line : str
        A line from some Lua source code.
    """

    # Matching spaces so that we don't pick up block comments (--[[ ]])
    return re.match(r"^--\s+", line)

def _convert_bool(b):
    """Converts Python bool values to Lua's.

    For simplicity's sake, you can use Python's bool values for everything in
    the codebase. Before it can go in the XML it has to be turned into a string,
    and it must also be lowercased to match Lua's bool values, otherwise ROBLOX
    won't recognize them.
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

def get_roblox_tag():
    """Gets the root <roblox> tag.

    This is what makes ROBLOX recognize the file as a Model that it can import,
    it should always be the first Element in the file. All others are appended
    to this tag.
    """

    # `version` is currently the only attribute that's required for ROBLOX to
    # recognize the file as a Model. All of the others are included to match
    # what ROBLOX outputs when  exporting a model to your computer.
    return ElementTree.Element("roblox", attrib={
        "xmlns:xmine": "http://www.w3.org/2005/05/xmlmime",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://www.roblox.com/roblox.xsd",
        "version": "4" })

def is_module(content):
    """Checks if the contents are from a Lua module.

    It looks for a returned value at the end of the file. If it finds one, it's
    safe to assume that it's a module.

    content : str
        The Lua source code to check.
    """

    # We match any number of whitespace after the `return` in case of accidental
    # spacing on the user's part.
    #
    # Then we match any characters to catch variables (`return module`) and
    # functions (`return setmetatable(t1, t2)`)
    #
    # We're optionally matching any number of spaces at the end of the file
    # incase of a final newline, or accidentally added spaces after the value.
    return re.search(r"return\s+.*(\s+)?$", content)

def get_script_type(content):
    """Checks a file's content to determine the type of Lua Script it is."""

    if is_module(content):
        return "ModuleScript"
    else:
        return "Script"

def tostring(element):
    """A more specialized version of ElementTree's `tostring`.

    We're using Unicode encoding so that this returns a string, instead of the
    default bytestring.

    We're also setting `short_empty_elements` to `False` so that all elements
    are output with their ending tags. This is only required when _writing_ the
    XML, as ROBLOX won't import the file if there are any self-closing tags.

    This function isn't used for writing, so while ending tags aren't mandatory,
    they're used here so the string version of the XML is consistent with what
    gets written.
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
        text : str|number|bool
            The contents of the property. For a Name or Source this will be a
            string, but you can also use Python's bool values with this, they
            just get converted to Lua's bools.
        """

        prop = ElementTree.SubElement(self.element, tag, name=name)
        prop.text = _sanitize(text)

        return prop

    def get(self, name):
        """Gets a property by its name.

        name : str
            The name of the property to search for. This would be "Name" for an
            instance's name, "Source" for the Lua source code, etc.
        """

        return self.element.find("*[@name='{}']".format(name))

    def set(self, name, new_value):
        """Changes the contents of a property to a new value."""

        prop = self.get(name)
        if prop is not None:
            prop.text = new_value

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

    def get_xml(self):
        return self.element

    def append_to(self, parent_element):
        """Appends the Element's XML to another Element.

        This is primarily used so that appending the XML of regular
        InstanceElement's and ModelElement's can be done from the same method.

        parent_element : Element
            The Element to append to.
        """

        xml = self.get_xml()
        parent_element.append(xml)

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
    """A container for other InstanceElements.

    This acts as a directory in-game. Other elements are parented to this one to
    construct the hierarchy.

    class_name="Folder" : str
        This can be any ROBLOX class.
        http://wiki.roblox.com/index.php?title=API:Class_reference
    name=None : str
        The name of the instance in-game. This will default to `class_name`.
    """

    def __init__(self, class_name="Folder", name=None):
        super().__init__(class_name, name)

class ModelElement(InstanceElement):
    def __init__(self, content):
        self.element = ElementTree.XML(content)

    def append_to(self, parent_element):
        """Imports the Model's contents into another Element.

        parent_element : Element
            The Element to append to.
        """

        xml = self.get_xml()

        # Because Models have their own <roblox> tag, when importing we have to
        # skip over that and just use the inner Elements.
        for element in list(xml):
            parent_element.append(element)
