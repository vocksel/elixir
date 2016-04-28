from xml.etree import ElementTree

"""Functions for creating ROBLOX instances in XML"""

def convert_bool(b):
    """Converts Python bool values to Lua's.

    This is used when inserting bool values in the XML. Lua's bool values are
    all lowercase
    """
    return str(b).lower()

class CustomElement:
    """An extension of the Element class.

    Element raises an AttributeError when we try to set anything on `self`,
    because of this we're _implementing_ it as a property, as opposed to
    inheriting from it directly.
    """

    def __init__(self, *args, **kwargs):
        self.element = ElementTree.Element(*args, **kwargs)

    def __repr__(self):
        # We're using Unicode encoding so that this returns a string, instead of
        # the default bytestring.
        #
        # We're also setting short_empty_elements to `False` so that all
        # elements are output with their ending tags. This is only required when
        # _writing_ the XML, as ROBLOX won't import the file it there are any
        # self-closing tags. This is done here so when the Element is turned
        # into a string, it is consistent with what it will be written as.
        return ElementTree.tostring(self.element, encoding="unicode",
            short_empty_elements=False)

class CustomSubElement(CustomElement):
    """Customized SubElement.

    This is purely just to inherit all of CustomElement's attributes so that
    SubElements can be converted to strings the same way that Elements can.
    """

    def __init__(self, *args, **kwargs):
        self.element = ElementTree.SubElement(*args, **kwargs)

class PropertyElement(CustomSubElement):
    """Container for the properties of InstanceElement.

    This stores things like the Instance's in-game name, and for Scripts it can
    hold the source code, as well as if the Script is disabled or not.
    """

    def __init__(self, parent):
        super().__init__(parent, "Properties")

        # I don't actually think I want to use SubElement at all. This makes it
        # tricker to test, as whenever I want to test this class I also need a
        # CustomElement to parent it to.

    def add(self, tag, name, text):
        """Add a new property.

        tag : str
            The type of property. This will typically be "string", "bool" or
            "ProtectedString".
        name : str
            The property's name. For example, you would use a tag of "bool" and
            a name of "Disabled" for the Disabled property of a Script.
        """

        prop = CustomSubElement(self.element, tag, name=name)
        prop.element.text = text

        return prop

class InstanceElement(CustomElement):
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
        super().__init__("Item", attrib={"class": class_name})

        self.properties = PropertyElement(self.element)
        self.name = self.properties.add("string", "Name", name)

class ScriptElement(InstanceElement):
    def __init__(self, class_name, name=None, source=None, disabled=False):
        # We need to convert `disabled` to a string so it can be used in the
        # XML. It must also be lowercased to match ROBLOX's bool values.
        disabled = str(disabled).lower()

        super().__init__(class_name, name)

        self.source = self.properties.add("ProtectedString", "Source", source)
        self.disabled = self.properties.add("bool", "Disabled", disabled)

def new_property(parent, prop_type, name, text):
    prop = ElementTree.SubElement(parent, prop_type, name=name)
    prop.text = text

    return prop

def create_instance_xml(class_name, name):
    # A "referent" used to be applied as an attribute, but it is no longer
    # needed. A referent is a sort of ID for each ROBLOX instance in the XML.
    # ROBLOX imports models just fine without them, so it's not necessary to
    # include.
    item = ElementTree.Element("Item", attrib={
        # `class` is a reserved keyword so we have to pass it in through this
        # dict rather than as a named parameter.
        "class": class_name
    })

    properties = ElementTree.SubElement(item, "Properties")
    new_property(properties, prop_type="string", name="Name", text=name)

    return item, properties

def create_script_xml(class_name, name, source, disabled=False):
    # This is a bool value and must be converted to a string so that it can
    # be written as XML.
    #
    # It must also be lowercased to match ROBLOX's bool values.
    disabled = str(disabled).lower()

    item, properties = create_instance_xml(class_name, name)

    new_property(properties, prop_type="ProtectedString", name="Source",
        text=source)

    new_property(properties, prop_type="bool", name="Disabled", text=disabled)

    return item
