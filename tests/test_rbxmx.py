from elixir.rbxmx import *

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

def _new_item(class_name=None):
    """Helper function for creating new `Item` Elements.

    This is used until we get to InstanceElement, where we then use that class
    for all of the elements instead instead.
    """
    class_name = class_name or "Folder"
    return ElementTree.Element("Item", attrib={ "class": class_name })

class TestBoolConversion:
    # I know the name sounds silly, but the function is used for putting bool
    # values into the XML, so it has to convert them into strings.
    def test_bool_is_string(self):
        assert type(convert_bool(True)) is str

    def test_bool_is_lowecased(self):
        assert convert_bool(True).islower() == True

class TestSanitization:
    def test_is_converting_bools(self):
        assert type(sanitize(True)) is str

    def test_is_returning_same_content_if_not_sanitize(self):
        # As of writing this, strings do not get sanitized in any way. If this
        # changes in the future this test will fail.
        content = "Hello, World!"
        sanitized_content = sanitize(content)

        assert content == sanitized_content

class TestModuleRecognition:
    content = "return value"

    def test_matches_module_with_excess_newlines(self):
        content = self.content + "\n\n\n\n"
        assert is_module(content)

    def test_matches_function_as_return_value(self):
        content = "return setmetatable(module, mt)"
        assert is_module(content)

class TestElementToStringConversion:
    def test_is_not_output_as_bytestring(self):
        item = _new_item()
        assert tostring(item) is not bytes

    def test_is_converting_to_string_properly(self):
        item = _new_item()
        expected_xml = "<Item class=\"Folder\"></Item>"
        assert tostring(item) == expected_xml

class TestPropertyElement:
    def test_can_add_properties(self):
        item = _new_item()
        properties = PropertyElement(item)
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
        name = self.instance.name.text
        assert class_name == name

    def test_has_properties(self):
        properties = self.element.find("Properties")
        assert properties

class TestScriptElement:
    instance = ScriptElement("Script", None, SCRIPT_SOURCE, True)
    element = instance.element
    properties = instance.properties

    def test_disabled_is_converted_properly(self):
        script = ScriptElement("")
        disabled = self.instance.disabled
        assert disabled.text == "true"

    def test_source_can_be_blank(self):
        script = ScriptElement("Script")
        expected_xml = "<ProtectedString name=\"Source\"></ProtectedString>"

        assert tostring(script.source) == expected_xml

    def test_can_have_source(self):
        script = ScriptElement("Script", source="print(\"Hello, World!\")")
        expected_xml = "<ProtectedString name=\"Source\">print(\"Hello, " \
            "World!\")</ProtectedString>"

        assert tostring(script.source) == expected_xml

    def test_can_have_varied_class_name(self):
        for script_class in [ "Script", "LocalScript", "ModuleScript" ]:
            script = ScriptElement(script_class)

            assert script.element.get("class") == script_class
