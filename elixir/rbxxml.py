from xml.etree import ElementTree

"""Functions for creating ROBLOX instances in XML"""

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
