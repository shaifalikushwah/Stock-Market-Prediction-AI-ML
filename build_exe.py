"""
PyInstaller Build Automation Script for Stock Market Screening & Analysis System.
Compiles main.py into a standalone Windows Executable (dist/StockScreenerAI/StockScreenerAI.exe).
"""

import sys
import subprocess
import os


def build_executable():
    print("=" * 60)
    print("Building Standalone Windows Executable using PyInstaller...")
    print("=" * 60)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(project_dir, "main.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=StockScreenerAI",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--paths={project_dir}",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
        "--exclude-module=notebook",
        "--exclude-module=jupyter",
        "--exclude-module=tkinter",
        "--exclude-module=PIL",
        "--hidden-import=PyQt6",
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.ensemble._forest",
        main_script
    ]

    print(f"Executing build command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=project_dir)

    if res.returncode == 0:
        exe_path = os.path.join(project_dir, "dist", "StockScreenerAI", "StockScreenerAI.exe")
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Standalone Executable Location: {exe_path}")
        print("=" * 60)
    else:
        print("\n" + "!" * 60)
        print("BUILD FAILED. Please check logs above.")
        print("!" * 60)


if __name__ == "__main__":
    build_executable()
