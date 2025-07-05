#!/usr/bin/env python3
"""
Setup script to install required dependencies for keyboard control
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("🔧 Setting up dependencies for keyboard control...")
    print("-" * 50)
    
    # Required packages
    packages = ["pygame"]
    
    success = True
    for package in packages:
        if not install_package(package):
            success = False
    
    print("-" * 50)
    if success:
        print("✅ All dependencies installed successfully!")
        print("You can now use keyboard control in the simulator.")
        print("\nTo test keyboard functionality, run:")
        print("  python test_keyboard.py")
        print("\nTo run the simulator:")
        print("  cd deploy_mujoco && python deploy_mujoco.py")
    else:
        print("❌ Some dependencies failed to install.")
        print("Please install them manually and try again.")

if __name__ == "__main__":
    main()
