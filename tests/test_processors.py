from elixir import processors

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
