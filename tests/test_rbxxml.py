from elixir.rbxxml import *

"""Tests for ROBLOX-related XML generation."""

SCRIPT_SOURCE = """
-- Name: Hello
-- ClassName: LocalScript

local module = {}

function module.hello(name)
  name = name or "World"
  return "Hello" .. name .. "!"
end

return module
"""

class TestBoolConversion:
    # I know the name sounds silly, but the function is used for putting bool
    # values into the XML, so it has to convert them into strings.
    def test_bool_is_string(self):
        assert type(convert_bool(True)) is str

    def test_bool_is_lowecased(self):
        assert convert_bool(True).islower() == True

class TestCustomElement:
    def test_is_not_output_as_bytestring(self):
        item = CustomElement("Item")
        assert str(item) is not bytes

    def test_is_converting_to_string_properly(self):
        item = CustomElement("Item", attrib={"class": "Folder"})
        expected_xml = "<Item class=\"Folder\"></Item>"
        assert str(item) == expected_xml

class TestPropertyElement:
    def test_can_add_properties(self):
        instance = CustomElement("Item")
        properties = PropertyElement(instance.element)
        properties.add(tag="string", name="Property", text="Value")
        prop = properties.element.find("*[@name='Property']")

        assert prop.text == "Value"

class TestInstanceElement:
    instance = InstanceElement("Folder")
    element = instance.element

    def test_has_class_name(self):
        assert "class" in self.element.attrib

    def test_class_name_is_set_properly(self):
        assert self.element.get("class") == "Folder"

    def test_name_matches_class_name_by_default(self):
        class_name = self.element.get("class")
        name = self.instance.name.element.text
        assert class_name == name

    def test_has_properties(self):
        properties = self.element.find("Properties")
        assert properties

class TestScriptElement:
    instance = ScriptElement("Script", None, SCRIPT_SOURCE, True)
    element = instance.element
    properties = instance.properties

    def test_disabled_is_converted_properly(self):
        disabled = self.instance.disabled.element
        assert disabled.text == "true"

    def test_source_can_be_blank(self):
        script = ScriptElement("Script")
        expected_xml = "<ProtectedString name=\"Source\"></ProtectedString>"

        assert str(script.source) == expected_xml
