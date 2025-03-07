#!/bin/bash

set -e  # Exit on error

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Install build dependencies
python3 -m pip install --upgrade pip build pyinstaller

# Create Python wheel package
python3 -m build

# Create Windows executable if running on Windows or Wine is available
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || command_exists wine; then
    echo "Building Windows executable..."
    if command_exists wine; then
        PYTHON="wine python"
    else
        PYTHON="python"
    fi
    $PYTHON -m PyInstaller --name=figma-converter \
        --windowed \
        --icon=figma-converter.ico \
        --add-data="figma-converter.png:figma_converter" \
        --hidden-import=customtkinter \
        --hidden-import=PIL \
        gui.py
    echo "Windows executable created in dist/figma-converter/"
fi

# Create Linux packages if running on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Install Linux packaging tools if not present
    if ! command_exists dpkg-deb || ! command_exists rpmbuild; then
        echo "Installing packaging tools..."
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y dpkg rpm
        elif command_exists dnf; then
            sudo dnf install -y dpkg rpm-build
        fi
    fi

    # Create DEB package
    echo "Building DEB package..."
    mkdir -p dist/deb/usr/bin
    mkdir -p dist/deb/usr/share/applications
    mkdir -p dist/deb/usr/share/icons/hicolor/256x256/apps
    
    cp dist/*.whl dist/deb/usr/bin/figma-converter
    cp figma-converter.desktop dist/deb/usr/share/applications/
    cp figma-converter.png dist/deb/usr/share/icons/hicolor/256x256/apps/
    
    cd dist/deb
    dpkg-deb --build . ../figma-converter.deb
    cd ../..

    # Create RPM package
    echo "Building RPM package..."
    mkdir -p dist/rpm/SPECS dist/rpm/SOURCES
    
    # Create RPM spec file
    cat > dist/rpm/SPECS/figma-converter.spec << 'EOF'
%define name figma-converter
%define version 1.0.0
%define release 1

Name: %{name}
Version: %{version}
Release: %{release}
Summary: Convert Figma designs to Tkinter GUI applications
License: MIT
URL: https://github.com/fraold/figma-converter
Source0: %{name}-%{version}.tar.gz
BuildArch: noarch
Requires: python3 >= 3.8

%description
A GUI application to convert Figma designs into Tkinter applications.

%prep
%setup -q

%install
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

cp figma-converter %{buildroot}/usr/bin/
cp figma-converter.desktop %{buildroot}/usr/share/applications/
cp figma-converter.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/

%files
/usr/bin/figma-converter
/usr/share/applications/figma-converter.desktop
/usr/share/icons/hicolor/256x256/apps/figma-converter.png
EOF

    # Create source tarball
    tar czf dist/rpm/SOURCES/figma-converter-1.0.0.tar.gz .
    
    # Build RPM package
    rpmbuild --define "_topdir $(pwd)/dist/rpm" -bb dist/rpm/SPECS/figma-converter.spec
    mv dist/rpm/RPMS/noarch/*.rpm dist/
fi

echo "Build complete! Distribution files are in the dist/ directory:"
ls -l dist/
