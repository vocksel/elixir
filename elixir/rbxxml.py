from xml.etree import ElementTree

"""Functions for creating ROBLOX instances in XML"""

def new_property(parent, prop_type, name, text):
    prop = ElementTree.SubElement(parent, prop_type, name=name)
    prop.text = text

    return prop

def create_item(class_name, name):
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

    return item
