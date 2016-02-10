import os.path

from elixir.rbx import is_module, Container, Model, Script

class BaseProcessor:
    """The primary processor class.

    A processor is what compilers use to determine what happens when they
    encounter a file or folder. All of the `process` methods return a new
    instance from `elixir.rbx`.

    For example, when processing a file, we return a new Script. The XML of
    these instances is then appended into the hierarchy when compiling.
    """

    def process_folder(self, path):
        """Processing for folders in the source directory.

        path : str
            The path to a folder.
        """

        folder_name = os.path.basename(path)
        return Container(folder_name)

    def process_model(self, path):
        return Model(path)

    def process_script(self, path):
        """Processing for Lua files in the source directory.

        path : str
            The path to a Lua file.
        """

        if is_module(path):
            return Script(path, class_name="ModuleScript")
        else:
            return Script(path)

class NevermoreProcessor(BaseProcessor):
    """Processor for NevermoreEngine (Legacy).

    This should be only used on or before commit b9b5a8 (linked below).
    Nevermore was refactored and no longer requries this special handling.

    This processor is kept here for legacy support.

    https://github.com/Quenty/NevermoreEngine/tree/b9b5a836e4b5801ba19abfa2a5eab79921076542
    """

    def process_script(self, path):
        filename = os.path.basename(path)
        if filename == "NevermoreEngineLoader.lua":
            return Script(path)
        elif ".main" in filename.lower():
            return Script(path, disabled=True)
        else:
            return Script(path, class_name="ModuleScript")
