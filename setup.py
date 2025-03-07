from setuptools import setup, find_packages

setup(
    name="figma-tkinter-converter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "semver>=3.0.1",
    ],
    entry_points={
        'console_scripts': [
            'figma-converter=gui:main',
        ],
    },
    author="MPS",
    author_email="support@mps.com",
    description="Convert Figma designs to Tkinter GUI applications",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="figma, tkinter, gui, converter, design",
    url="https://github.com/fraold/figma-converter",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: User Interfaces",
    ],
    package_data={
        'figma_converter': ['*.png', '*.ico', '*.desktop'],
    },
    data_files=[
        ('share/applications', ['figma-converter.desktop']),
        ('share/icons/hicolor/256x256/apps', ['figma-converter.png']),
    ],
)
