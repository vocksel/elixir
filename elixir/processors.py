import os.path

from elixir import rbxmx

class BaseProcessor:
    """The primary processor class.

    A processor is what compilers use to determine what happens when they
    encounter a file or folder. All of the `process` methods return a new
    instance from `elixir.rbx`.

    For example, when processing a file, we return a new Script. The XML of
    these instances is then appended into the hierarchy when compiling.
    """

    def process_folder(self, name):
        """Processing for folders in the source directory.

        name : str
            The name of the folder to process. Excluding the extension.
        """

        return rbxmx.ContainerElement(name=name)

    def process_model(self, content):
        """Processing for ROBLOX Model files (.rbxmx).

        content : str
            The contents of the Model file.
        """

        return rbxmx.ModelElement(content)

    def _get_script_class(self, content):
        if rbxmx.is_module(content):
            return "ModuleScript"
        else:
            return "Script"

    def process_script(self, name, content):
        """Processing for Lua files in the source directory.

        name : str
            The name of the Script.
        content : str
            The Lua source code.
        """

        class_name = self._get_script_class(content)

        script = rbxmx.ScriptElement(class_name, name=name, source=content)
        script.use_embedded_properties()

        return script

class NevermoreProcessor(BaseProcessor):
    """Processor for NevermoreEngine (Legacy).

    This should be only used on or before commit b9b5a8 (linked below).
    Nevermore was refactored and no longer requries this special handling.

    This processor is kept here for legacy support.

    https://github.com/Quenty/NevermoreEngine/tree/b9b5a836e4b5801ba19abfa2a5eab79921076542
    """

    def process_script(self, name, content):
        if name == "NevermoreEngineLoader":
            return rbxmx.ScriptElement(name=name, source=content)
        elif ".main" in name.lower():
            return rbxmx.ScriptElement(name=name, source=content, disabled=True)
        else:
            return rbxmx.ScriptElement("ModuleScript", name=name, source=content)
