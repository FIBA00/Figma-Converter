# Figma to Tkinter Converter

A powerful tool to convert Figma designs into Tkinter GUI applications. Available in both CLI and GUI modes.

## Features

- Convert Figma designs to Tkinter code
- Modern CustomTkinter-based GUI
- Command-line interface support
- Auto-save configuration
- Dark/Light mode support
- Fullscreen and window mode

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Converter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode
Run the application in GUI mode:
```bash
python gui.py
```

### CLI Mode
Run the application in command-line mode:
```bash
python figma.py
```

## Requirements

- Python 3.8+
- Figma Access Token (Get it from your Figma account settings)
- Valid Figma file URL

## Configuration

The application automatically saves your last used configuration in the `GUI_DIR/config.json` file.

## License

