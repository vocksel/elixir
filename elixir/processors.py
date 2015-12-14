import os.path

from elixir.rbx import Container, Model, Script

class BaseProcessor:
    """The primary processor class.

    A processor is what compilers use to determine what happens when they
    encounter a file or folder. All of the `process` methods return a new
    instance from `elixir.rbx`.

    For example, when processing a file, we return a new Script. The XML of
    these instances is then appended into the hierarchy when compiling.

    model_name :
    """

    def __init__(self, model_name):
        self.model_name = model_name

    def get_base_container(self):
        """Gets the container that will hold all of the source code.

        Typically, you won't want the name of the root folder to be the name of
        the source folder that you passed in to the compiler. Instead of having
        a structure of:

            src/
              SomeScript.lua
              AnotherScript.lua

        This will return a new Container with the name of `model_name`, so you
        can properly name your project in-game. Like so:

            ProjectName/ <- This depends on what was set for `model_name`
              SomeScript.lua
              AnotherScript.lua
        """

        return Container(self.model_name)

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

        return Script(path)

class NevermoreProcessor(BaseProcessor):
    """Processor for NevermoreEngine.

    https://github.com/Quenty/NevermoreEngine
    """

    def __init__(self, model_name):
        self.model_name = "Nevermore"

    def process_script(self, path):
        filename = os.path.basename(path)
        if filename == "NevermoreEngineLoader.lua":
            return Script(path)
        elif ".main" in filename.lower():
            return Script(path, disabled=True)
        else:
            return Script(path, class_name="ModuleScript")
