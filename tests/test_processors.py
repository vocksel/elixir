from elixir import processors
from elixir import rbxmx

MODEL_SOURCE = """\
<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">
	<External>null</External>
	<External>nil</External>
	<Item class="Folder" referent="RBXCB30D4696C69484A9B4117C6A5910E7E">
		<Properties>
			<string name="Name">Folder</string>
		</Properties>
		<Item class="Script" referent="RBX2484D10C2F394A178AC8CD7A84FFC2C2">
			<Properties>
				<bool name="Disabled">false</bool>
				<Content name="LinkedSource"><null></null></Content>
				<string name="Name">Script</string>
				<string name="ScriptGuid"></string>
				<ProtectedString name="Source"><![CDATA[print("Hello world!")
]]></ProtectedString>
			</Properties>
		</Item>
	</Item>
</roblox>
"""

class TestGettingFileContents:
    def test_can_get_file_contents(self, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("Content")

        content = processors._get_file_contents(str(f))

        assert content == "Content"

    def test_does_not_error_if_path_does_not_exist(self):
        fake_path = "/a/b/c"
        content = processors._get_file_contents(fake_path)

        assert content is None

class TestBaseProcessor:
    processor = processors.BaseProcessor()

    def test_compiles_folders(self):
        folder = self.processor.process_folder("Test")

        assert folder.name.text == "Test"
        assert folder.element.attrib.get("class") == "Folder"

    def test_compiles_models(self, tmpdir):
        f = tmpdir.join("Model.rbxmx")
        f.write(MODEL_SOURCE)
        model = self.processor.get_element(str(f))

        assert type(model) == rbxmx.ModelElement

    def test_compiles_server_scripts(self, tmpdir):
        f = tmpdir.join("Script.lua")
        f.write("print(\"Hello, World!\")")
        script = self.processor.get_element(str(f))

        assert type(script) == rbxmx.ScriptElement

class TestNevermoreProcessor:
    processor = processors.NevermoreProcessor()

    def test_engine_loader_is_enabled(self):
        """Handling for the main Nevermore loader.

        When we encounter `NevermoreEngineLoader.lua` we need to make sure a
        non-disabled Script is output.
        """

        name = "NevermoreEngineLoader"
        script = self.processor.process_script(name, "")

        assert script.disabled.text == "false"

    def test_all_other_scripts_are_disabled(self):
        script = self.processor.process_script("Script", "")

        assert script.disabled.text == "true"
