from xml.etree import ElementTree

"""Functions for creating ROBLOX instances in XML"""

def convert_bool(b):
    """Converts Python bool values to Lua's.

    Before we can insert a bool value in the XML, it must first be converted to
    a string and then lowercased to match Lua's bool values.
    """
    return str(b).lower()

def sanitize(content):
    """Makes sure `content` is safe to go in the XML.

    This is mostly for converting Python types into something XML compatible.
    """

    if type(content) == bool:
        return convert_bool(content)
    else:
        return content

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
        prop.text = sanitize(text)

        return prop

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
    def __init__(self, class_name, name=None, source=None, disabled=False):
        super().__init__(class_name, name)

        self.source = self.properties.add("ProtectedString", "Source", source)
        self.disabled = self.properties.add("bool", "Disabled", disabled)