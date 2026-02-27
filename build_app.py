import os
import subprocess
import sys

def build():
    print("Building Knowledgedock Application...")
    
    # Define paths
    main_script = "main.py"
    assets_dir = "assets"
    icon_file = os.path.join(assets_dir, "cover.png") # Using png if ico is not available, PyInstaller handles it
    
    # Add hidden imports if necessary
    hidden_imports = [
        "PyQt5.QtWebEngineWidgets",
        "sqlite3",
    ]
    
    # Construct PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--icon={icon_file}",
        "--name=Knowledgedock",
        f"--add-data={assets_dir}{os.pathsep}{assets_dir}",
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
        
    cmd.append(main_script)
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild completed successfully!")
        print("You can find the executable in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
    except FileNotFoundError:
        print("\nError: PyInstaller not found. Please install it with 'pip install pyinstaller'.")

if __name__ == "__main__":
    build()
