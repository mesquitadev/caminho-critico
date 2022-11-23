import sys

from cx_Freeze import setup, Executable

build_exe_options = {"packages": ["os", "sys"], "includes": ["networkx"]}
base = None
if sys.platform == "win37":
    base = "Win32GUI"

setup(
    name="grafo_csv",
    version="1.0",
    description="Mapa de rotinas",
    options={"build_exe": build_exe_options},
    executables=[Executable(".\main.py", base=base)]
)
