from setuptools import setup

setup(
    name="elixir",
    version="1.1.0",
    description="Turn directories and Lua files into a ROBLOX compatible XML file.",
    author="David Minnerly",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.4",
    ],
    keywords="lua roblox compiler",
    packages=["elixir"],
    entry_points={
        "console_scripts": [ "elixir=elixir.cli:main" ]
    }
)
