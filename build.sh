#!/bin/bash

set -e  # Exit on error

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Clean previous builds
rm -rf dist/*.deb

# # Create Windows executable if running on Windows or Wine is available
# if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || command_exists wine; then
#     echo "Building Windows executable..."
#     if command_exists wine; then
#         # Ensure Wine Python and PyInstaller are available
#         WINE_PYTHON="$HOME/.wine/drive_c/Python312/python.exe"
#         if [ ! -f "$WINE_PYTHON" ]; then
#             echo "Wine Python not found. Please install Python in Wine first."
#             exit 1
#         fi
        
#         # Install required packages in Wine Python
#         wine "$WINE_PYTHON" -m pip install pyinstaller customtkinter pillow requests semver
        
#         # Run PyInstaller through Wine
#         wine "$WINE_PYTHON" -m PyInstaller \
#             --name=figma-converter \
#             --windowed \
#             --icon=figma-converter.ico \
#             --add-data="figma-converter.png;." \
#             --hidden-import=customtkinter \
#             --hidden-import=PIL \
#             --hidden-import=requests \
#             --hidden-import=semver \
#             gui.py
#     else
#         echo "Wine is not installed. Skipping Windows build."
#         echo "installing the wine python exe"
#         wget https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe -O python-installer.exe
#     fi
#     echo "Windows executable created in dist/figma-converter/"
# fi

# Create DEB package
echo "Building DEB package..."

# Install dpkg if not present
if ! command_exists dpkg-deb; then
    echo "Installing dpkg..."
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y dpkg
    fi
fi

# Create directory structure
echo "Creating package structure..."
mkdir -p dist/deb/DEBIAN
mkdir -p dist/deb/usr/local/bin
mkdir -p dist/deb/usr/share/applications
mkdir -p dist/deb/usr/share/icons/hicolor/256x256/apps
mkdir -p dist/deb/usr/lib/figma-converter

# Create control file
cat > dist/deb/DEBIAN/control << EOF
Package: figma-converter
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-tk
Maintainer: Fraol D <fraold@example.com>
Description: Figma to Tkinter Converter
 A GUI application to convert Figma designs into Tkinter applications.
EOF

# Copy Python packages during build
echo "Copying Python packages..."
VENV_SITE_PACKAGES="venv/lib/python3.12/site-packages"
mkdir -p dist/deb/opt/figma-converter/lib

# Copy main packages
SYS_PACKAGES=("customtkinter" "requests" "semver" "darkdetect")
for pkg in "${SYS_PACKAGES[@]}"; do
    if [ -d "$VENV_SITE_PACKAGES/$pkg" ]; then
        echo "Copying $pkg from virtual environment"
        cp -r "$VENV_SITE_PACKAGES/$pkg" dist/deb/opt/figma-converter/lib/
    else
        echo "Warning: Package $pkg not found in virtual environment"
    fi
done

# Copy dependencies
for dep in "packaging" "urllib3" "idna" "charset_normalizer" "certifi"; do
    if [ -d "$VENV_SITE_PACKAGES/$dep" ]; then
        echo "Copying dependency $dep from virtual environment"
        cp -r "$VENV_SITE_PACKAGES/$dep" dist/deb/opt/figma-converter/lib/
    fi
done

# Create postinst script
cat > dist/deb/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e

# Update PYTHONPATH in launcher
sed -i "s|^python3|PYTHONPATH=/opt/figma-converter/lib python3|g" /usr/local/bin/figma-converter
EOF

# Make postinst executable
chmod 755 dist/deb/DEBIAN/postinst

# Create prerm script to clean up application directory
cat > dist/deb/DEBIAN/prerm << 'EOF'
#!/bin/bash
set -e

# Remove application directory if it exists
if [ -d "/opt/figma-converter" ]; then
    rm -rf "/opt/figma-converter"
fi
EOF

# Make prerm executable
chmod 755 dist/deb/DEBIAN/prerm

# Copy application files
echo "Copying application files..."
cp -r *.py dist/deb/usr/lib/figma-converter/
cp figma-converter.desktop dist/deb/usr/share/applications/
cp figma-converter.png dist/deb/usr/share/icons/hicolor/256x256/apps/

# Create launcher script
cat > dist/deb/usr/local/bin/figma-converter << 'EOF'
#!/bin/bash
python3 /usr/lib/figma-converter/gui.py "$@"
EOF

# Make launcher executable
chmod 755 dist/deb/usr/local/bin/figma-converter

# Build the package
echo "Building DEB package..."
dpkg-deb --build dist/deb dist/figma-converter.deb

echo "DEB package created in dist/figma-converter.deb"

echo "Build complete! Distribution files are in the dist/ directory:"
ls -l dist/
