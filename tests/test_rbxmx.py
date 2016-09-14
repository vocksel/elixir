from textwrap import dedent
from xml.etree import ElementTree

from elixir import rbxmx

"""Tests for ROBLOX-related XML generation."""

SCRIPT_SOURCE = """\
-- Name: Hello
-- ClassName: ModuleScript

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
        assert type(rbxmx._convert_bool(True)) is str

    def test_bool_is_lowecased(self):
        assert rbxmx._convert_bool(True).islower() == True

class TestSanitization:
    def test_is_converting_bools(self):
        assert type(rbxmx._sanitize(True)) is str

    def test_is_returning_same_content_if_not_sanitize(self):
        # As of writing this, strings do not get sanitized in any way. If this
        # changes in the future this test will fail.
        content = "Hello, World!"
        sanitized_content = rbxmx._sanitize(content)

        assert content == sanitized_content

class TestModuleRecognition:
    content = "return value"

    def test_matches_module_with_excess_newlines(self):
        content = self.content + "\n\n\n\n"
        assert rbxmx.is_module(content)

    def test_matches_function_as_return_value(self):
        content = "return setmetatable(module, mt)"
        assert rbxmx.is_module(content)

class TestGettingTheTypeOfScript:
    def test_recognizes_modules(self):
        content = dedent("""\
            local function hello()
                return "Hello, World!"
            end

            return hello""")

        assert rbxmx.get_script_class(content) == "ModuleScript"

class TestBaseTag:
    def test_has_necessary_attributes(self):
        tag = rbxmx.get_roblox_tag()

        # Currently this is the only attribute that's required for ROBLOX to
        # recognize the file as a Model.
        assert tag.get("version")

class TestElementToStringConversion:
    def test_is_not_output_as_bytestring(self):
        item = _new_item()
        assert rbxmx.tostring(item) is not bytes

    def test_is_converting_to_string_properly(self):
        item = _new_item()
        expected_xml = "<Item class=\"Folder\"></Item>"
        assert rbxmx.tostring(item) == expected_xml

class TestPropertyElement:
    def test_can_add_properties(self):
        item = _new_item()
        properties = rbxmx.PropertyElement(item)
        properties.add(tag="string", name="Property", text="Value")
        prop = properties.element.find("*[@name='Property']")

        assert prop.text == "Value"

    def test_can_get_properties_by_name(self):
        item = _new_item()
        properties = rbxmx.PropertyElement(item)
        properties.add(tag="string", name="Name", text="Property")

        prop = properties.get("Name")

        assert prop.text == "Property"

    def test_can_set_property_values(self):
        item = _new_item()
        properties = rbxmx.PropertyElement(item)
        properties.add(tag="string", name="Name", text="Property")
        prop = properties.get("Name")

        properties.set("Name", "Testing")

        assert prop.text == "Testing"

class TestInstanceElement:
    instance = rbxmx.InstanceElement("Folder")
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

    def test_getting_the_internal_element_reference(self):
        element = self.instance.get_xml()
        assert element == self.instance.element

    def test_appending_to_other_elements(self):
        element = rbxmx.InstanceElement("Folder")
        another_element = rbxmx.InstanceElement("Model")

        xml = another_element.get_xml()

        element.append_to(xml)

        xml_was_appeneded = xml.find("Item")

        assert xml_was_appeneded

class TestScriptElement:
    def test_disabled_is_converted_properly(self):
        script = rbxmx.ScriptElement("Script", disabled=True)
        assert script.disabled.text == "true"

    def test_source_can_be_blank(self):
        script = rbxmx.ScriptElement("Script", source=None)
        expected_xml = "<ProtectedString name=\"Source\"></ProtectedString>"

        assert rbxmx.tostring(script.source) == expected_xml

    def test_can_have_source(self):
        script = rbxmx.ScriptElement("Script",
            source="print(\"Hello, World!\")")
        expected_xml = "<ProtectedString name=\"Source\">print(\"Hello, " \
            "World!\")</ProtectedString>"

        assert rbxmx.tostring(script.source) == expected_xml

    def test_can_have_varied_class_name(self):
        for script_class in [ "Script", "LocalScript", "ModuleScript" ]:
            script = rbxmx.ScriptElement(script_class)

            assert script.element.get("class") == script_class

class TestScriptCommentMatching:
    def test_can_match_first_comment(self):
        comment = dedent("""\
            -- Name: SomeScript
            -- ClassName: LocalScript

            print("Hello, World!")""")

        expected_output = dedent("""\
            -- Name: SomeScript
            -- ClassName: LocalScript""")

        script = rbxmx.ScriptElement(source=comment)
        first_comment = script.get_first_comment()

        assert first_comment == expected_output

    def test_does_not_error_without_source(self):
        script = rbxmx.ScriptElement() # No `source` argument
        comment = script.get_first_comment()

        assert comment is None

    def test_does_not_error_without_first_comment(self):
        source = dedent("""\
            local function hello()
                return "Hello, World!"
            end

            return hello""")

        script = rbxmx.ScriptElement(source=source)
        comment = script.get_first_comment()

        assert comment is None

    def test_does_not_match_block_comments(self):
        """
        Right now, comment matching is only done to inline comments for
        simplicity. If a more sophisticated pattern is implemented to pick up
        block comments, this test can be removed.
        """

        comment = dedent("""\
            --[[
              Hello, World!
            --]]""")

        script = rbxmx.ScriptElement(source=comment)
        first_comment = script.get_first_comment()

        assert first_comment is None

class TestEmbeddedScriptProperties:
    def test_can_get_embedded_properties(self):
        source = dedent("""\
            -- Name: HelloWorld
            -- ClassName: LocalScript

            print("Hello, World!")""")

        script = rbxmx.ScriptElement(source=source)
        properties = script.get_embedded_properties()

        assert properties["Name"] == "HelloWorld"
        assert properties["ClassName"] == "LocalScript"

    def test_can_use_only_one_embedded_property(self):
        source = "-- ClassName: LocalScript"

        script = rbxmx.ScriptElement(source=source)
        properties = script.get_embedded_properties()

        assert properties["ClassName"] == "LocalScript"

    def test_does_not_detect_regular_comments_as_embedded_properties(self):
        source = "-- This is a comment"

        script = rbxmx.ScriptElement(source=source)
        properties = script.get_embedded_properties()

        assert not properties

    def test_is_overriding_with_embedded_properties(self):
        source = dedent("""\
            -- Name: HelloWorld
            -- ClassName: LocalScript

            print("Hello, World!")""")

        script = rbxmx.ScriptElement(name="SampleScript", source=source)

        assert script.name.text == "SampleScript"

        script.use_embedded_properties()

        assert script.name.text == "HelloWorld"

    def test_can_attempt_to_override_without_embedded_properties(self):
        source = dedent("""\
            local function hello()
                return "Hello, World!"
            end

            return hello""")

        script = rbxmx.ScriptElement(source=source)
        script.use_embedded_properties()

    def test_fails_graceully_for_property_that_doesnt_exist(self):
        source = "-- NonExistentProperty: true"

        script = rbxmx.ScriptElement(source=source)
        script.use_embedded_properties()
