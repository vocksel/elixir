import os.path

from elixir import rbxmx

def _get_file_contents(path):
    if os.path.isfile(path):
        with open(path) as f:
            return f.read()

class BaseProcessor:
    """The primary processor class.

    A processor is what compilers use to determine what happens when they
    encounter a file or folder. All of the `process` methods return a new
    instance from `elixir.rbxmx`.

    For example, when processing a file, we return a new Script. The XML of
    these instances is then appended into the hierarchy when compiling.
    """

    def process_folder(self, name):
        """Processing for folders.

        name : str
            The name of the folder to process.
        """

        return rbxmx.ContainerElement(name=name)

    def process_model(self, content):
        """Processing for ROBLOX Model files (.rbxmx).

        content : str
            The contents of the Model file.
        """

        return rbxmx.ModelElement(content)

    def process_script(self, name, content):
        """Processing for Lua files.

        name : str
            The name of the Script.
        content : str
            The Lua source code.
        """

        class_name = rbxmx.get_script_type(content)

        script = rbxmx.ScriptElement(class_name, name=name, source=content)
        script.use_embedded_properties()

        return script

    def get_element(self, path):
        """Returns a Python instance representing a ROBLOX instance.

        This routes `path` to the most appropriate `process` method and returns
        one of the classes from `rbxmx`.

        path : str
            The path to a folder or file to be processed.
        """

        name = os.path.basename(path)

        if os.path.isdir(path):
            return self.process_folder(name)
        else:
            name, ext = os.path.splitext(name)
            content = _get_file_contents(path)

            if ext == ".lua":
                return self.process_script(name, content)
            elif ext == ".rbxmx":
                return self.process_model(content)

class NevermoreProcessor(BaseProcessor):
    """Processor for NevermoreEngine (Legacy).

    This should be only used on or before commit b9b5a8 (linked below).
    Nevermore was refactored and no longer requries this special handling.

    This processor is kept here for legacy support.

    https://github.com/Quenty/NevermoreEngine/tree/b9b5a836e4b5801ba19abfa2a5eab79921076542
    """

    def process_script(self, name, content):
        script = super().process_script(name, content)

        # This is the name of the Script that loads Nevermore. It sets the
        # Disabled property to `false` for Scripts that it determines should
        # run. All Scripts need to be disabled by default for this handling.
        is_engine_loader = name == "NevermoreEngineLoader"

        is_module = script.element.attrib.get("class") == "ModuleScript"

        if not is_engine_loader and not is_module:
            script.disabled.text = "true"

        return script
