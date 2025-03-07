"""
- Figma design to tkinter app converter version 1.0
- The premium version will come in the next release.
"""
import os
import sys
import platform
import json
import logging
import subprocess
import requests
import semver
import customtkinter as ctk
from threading import Thread
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from typing import Dict, List

from figma import (
    create_path,
    convert_url_to_file_format,
    load_config,
    save_config,
    converter,
    DATA_DIR,
    CONFIG_PATH,
)
def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    if getattr(sys, "frozen", False):
        # We are running in a PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # We are running in normal Python environment
        return Path(__file__).parent

sys.path.append(str(get_project_root()))
PATHS: Dict[str, Path] = {"logs": DATA_DIR / "logs" / "app.log"}
PATHS["logs"].parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            str(PATHS["logs"])
        ),  # Convert Path to string for FileHandler
        logging.StreamHandler(),
    ],
)


class FigmaConverterApp(ctk.CTk):
    GITHUB_REPO = "fraold/figma-converter"  # Default repository
    CURRENT_VERSION = "1.0.0"
    GITHUB_API_URL = "https://api.github.com/repos/"

    def __init__(self):
        super().__init__()
        self.root = get_project_root()
        self.default_dir = DATA_DIR
        self.default_dir.mkdir(parents=True, exist_ok=True)
        self.title("MPS Figma to tkinter convertor")
        self.wm_attributes("-type", "splash")

        # Check for updates on startup
        self.auto_save = ctk.BooleanVar(value=True)  # by default Save
        self.active_tooltip = None  # Track current tooltip
        self.tooltip_after_id = None  # Track scheduled tooltipe_after_id
        self.sidebar_width = 250
        self.update_available = False
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Set geometry
        # self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(1000, 800)  # Minimum window size
        self.grid_columnconfigure(1, weight=1)  # Make column 1 expandable
        self.grid_rowconfigure(5, weight=1)  # Make the last row expandable for output
        self.top_bar = ctk.CTkFrame(self, height=40, fg_color=("transparent"))
        self.top_bar.grid(
            row=0, column=0, columnspan=2, sticky="new", padx=10, pady=(5, 0)
        )
        self.top_bar.grid_columnconfigure(
            3, weight=1
        )  # make the middle section expandable
        # app icon/logo
        self.app_icon = ctk.CTkLabel(self.top_bar, text="🎨", font=ctk.CTkFont(size=20))
        self.app_icon.grid(row=0, column=0, padx=5)

        # app name
        self.app_name = ctk.CTkLabel(
            self.top_bar, text="Converter", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.app_name.grid(row=0, column=1, padx=5, pady=5)

        # app version info
        self.version_label = ctk.CTkLabel(
            self.top_bar,
            text="v1.0.0",
            font=ctk.CTkFont(size=12),
        )
        self.version_label.grid(row=0, column=2, padx=5, pady=5)

        # status indicator (middle, expandable)
        self.status_label = ctk.CTkLabel(
            self.top_bar,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("green", "light green"),
        )
        self.status_label.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        # help button
        self.help_button = ctk.CTkButton(
            self.top_bar,
            text="?",
            width=30,
            height=30,
            command=self.show_help,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.help_button.grid(row=0, column=4, padx=5, pady=5)

        # Minimize button
        self.min_button = ctk.CTkButton(
            self.top_bar,
            text="─",
            width=30,
            height=30,
            command=self.minimize_window,
            fg_color=("red", "dark red"),
            hover_color=("gray70", "gray30"),
        )
        self.min_button.grid(row=0, column=5, padx=2)

        # Maximize button
        self.max_button = ctk.CTkButton(
            self.top_bar,
            text="□",
            width=30,
            height=30,
            command=self.toggle_maximize,
            fg_color=("red", "dark red"),
            hover_color=("gray70", "gray30"),
        )
        self.max_button.grid(row=0, column=6, padx=2)

        # Close button
        self.close_button = ctk.CTkButton(
            self.top_bar,
            text="×",
            width=30,
            height=30,
            command=self.quit,
            fg_color=("red", "dark red"),
            hover_color=("dark red", "red"),
        )
        self.close_button.grid(row=0, column=7, padx=2)
        self.toggle_maximize()

        # Make window draggable from top bar
        self.top_bar.bind("<Button-1>", self.start_move)
        self.top_bar.bind("<B1-Motion>", self.on_move)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(
            self, width=self.sidebar_width, corner_radius=2
        )
        self.sidebar_frame.grid(
            row=0, column=0, rowspan=7, sticky="nsew", padx=0, pady=0
        )
        self.sidebar_frame.grid_propagate(False)  # Prevent sidebar from shrinking
        self.sidebar_frame.configure(
            corner_radius=5,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color=("gray85", "gray20"),
        )
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        # Toggle button at the top of sidebar
        self.toggle_button = ctk.CTkButton(
            self.sidebar_frame,
            text="≡",
            width=30,
            height=30,
            command=self.toggle_sidebar,
            font=ctk.CTkFont(size=20),
        )
        self.toggle_button.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

        # Sidebar content frame (to make hiding content easier)
        self.sidebar_content = ctk.CTkFrame(
            self.sidebar_frame, fg_color="transparent", corner_radius=0
        )
        self.sidebar_content.grid(row=1, column=0, sticky="nw", padx=0, pady=0)
        self.sidebar_content.grid_rowconfigure(
            13, weight=1
        )  # allow expansion at the bottom
        self.sidebar_content.configure(
            border_width=2, border_color=("gray70", "gray30")
        )
        self.sidebar_expanded = True
        self.toggle_sidebar()

        # Sidebar content
        self.logo_label = ctk.CTkLabel(
            self.sidebar_content,
            text="Mk LLC: Figma converter",
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=400,
        )
        self.logo_label.grid(row=0, column=0, padx=10, pady=(10, 10))

        self.explanation_label = ctk.CTkLabel(
            self.sidebar_content,
            text="This app is for converting figma designs to tkinter GUI",
            font=ctk.CTkFont(size=12),
            wraplength=160,
        )
        self.explanation_label.grid(row=1, column=0, padx=10, pady=(5, 5))

        # add a separator line
        self.separator = ctk.CTkFrame(self.sidebar_content, height=2)
        self.separator.grid(row=2, column=0, padx=2, pady=(2, 2), sticky="ew")

        # after separater we need small frame to contain the settings that way we have styled arrangement
        self.settings_content = ctk.CTkFrame(
            self.sidebar_content, fg_color="transparent"
        )
        self.settings_content.grid(
            row=3, column=0, rowspan=5, padx=(5, 5), pady=(10, 0)
        )
        self.settings_content.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # settings section label
        self.settings_label = ctk.CTkLabel(self.settings_content)
        self.settings_label.grid(row=0, column=0, padx=10, pady=(10, 5))
        self.settings_label.configure(
            text="⚙️ Settings", font=ctk.CTkFont(size=16, weight="bold")
        )

        # auto save checkbox
        self.auto_save_cb = ctk.CTkCheckBox(
            self.settings_content,
            text="Auto-save settings",
            variable=self.auto_save,
            command=self.toggle_auto_save,
        )
        self.auto_save_cb.grid(row=4, column=0, padx=20, pady=5)

        # Manual save button
        self.save_button = ctk.CTkButton(
            self.settings_content,
            text="Save settings",
            command=self.save_settings,
            height=28,
        )
        self.save_button.grid(row=5, column=0, padx=20, pady=5)
        self.apply_button_style(self.save_button, "primary")

        # manual load button
        self.load_button = ctk.CTkButton(
            self.settings_content,
            text="Load settings",
            command=self.load_settings,
            height=28,
        )
        self.load_button.grid(row=6, column=0, padx=20, pady=5)
        self.apply_button_style(self.load_button, "primary")

        # clear settings button
        self.clear_button = ctk.CTkButton(
            self.settings_content,
            text="Clear settings",
            command=self.clear_settings,
            height=28,
        )
        self.clear_button.grid(row=7, column=0, padx=20, pady=5)
        self.apply_button_style(self.clear_button, "primary")

        # export settings button
        self.export_button = ctk.CTkButton(
            self.settings_content,
            text="Export Settings",
            command=self.export_settings,
            height=28,
        )
        self.export_button.grid(row=8, column=0, padx=20, pady=5)
        self.apply_button_style(self.export_button, "primary")

        # Add another separator
        self.separator2 = ctk.CTkFrame(self.sidebar_content, height=2)
        self.separator2.grid(row=8, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Recent conversions section
        self.recent_label = ctk.CTkLabel(
            self.sidebar_content,
            text="🕒 Recent Conversions",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.recent_label.grid(row=9, column=0, padx=20, pady=(10, 5))

        # List to show recent conversions
        self.recent_list = ctk.CTkTextbox(self.sidebar_content, height=150, width=200)
        self.recent_list.grid(row=10, column=0, padx=20, pady=5)
        self.recent_list.configure(state="disabled")  # Make it read-only

        # show tool tip
        for widget, text in [
            (self.save_button, "Save current token and URL"),
            (self.clear_button, "Clear all saved settings"),
            (self.auto_save_cb, "Automatically save settings after conversion"),
        ]:
            widget.bind("<Enter>", lambda e, t=text: self.show_tooltip(t))
            widget.bind("<Leave>", lambda e: self.cancel_tooltip())

        # theme switcher section
        self.separator3 = ctk.CTkFrame(self.sidebar_content, height=2)
        self.separator3.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.theme_var = ctk.StringVar(value="light")
        self.theme_label = ctk.CTkLabel(
            self.sidebar_content,
            text="🎨 Appearance",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.theme_label.grid(row=12, column=0, padx=20, pady=(10, 5))

        self.theme_switch = ctk.CTkSwitch(
            self.sidebar_content,
            text="Dark Mode",
            command=self.toggle_theme,
            variable=self.theme_var,
            onvalue="dark",
            offvalue="light",
        )
        self.theme_switch.grid(row=12, column=0, padx=20, pady=5)

        # Main content frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(
            row=1, column=1, rowspan=4, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Input fields in main frame
        self.token_label = ctk.CTkLabel(
            self.main_frame, text="Figma Token:", anchor="w"
        )
        self.token_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        self.token_entry = ctk.CTkEntry(
            self.main_frame, placeholder_text="Enter your figma token"
        )
        self.token_entry.grid(row=1, column=0, padx=20, pady=(5, 20), sticky="ew")

        self.url_label = ctk.CTkLabel(self.main_frame, text="Figma URL:", anchor="w")
        self.url_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.main_frame, placeholder_text="Enter your figma url"
        )
        self.url_entry.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Convert button
        self.convert_button = ctk.CTkButton(
            self.main_frame,
            text="Convert Design",
            command=self.convert_design,
            height=32,
        )
        self.convert_button.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Output textbox at the bottom
        self.output_textbox = ctk.CTkTextbox(
            self,
            height=200,
        )
        self.output_textbox.grid(row=5, column=1, padx=20, pady=(0, 20), sticky="nsew")
        self.output_textbox.configure(state="disabled")

        # bottom bar frame
        self.bottom_bar = ctk.CTkFrame(
            self, corner_radius=2, fg_color=("gray85", "gray20"), height=100
        )
        self.bottom_bar.grid(row=6, column=1, columnspan=2, padx=0, pady=0, sticky="ew")
        self.bottom_bar.grid_columnconfigure(
            1, weight=1
        )  # allow the progress bar to expand
        self.bottom_bar.grid_propagate(False)  # prevent frame from shrinking

        # progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self.bottom_bar)
        self.progress_bar.grid(row=0, column=1, padx=(20, 20), pady=5, sticky="ew")
        # Configure the progress bar
        self.progress_bar.configure(
            mode="indeterminate",  # For continuous animation
            progress_color=("red", "red"),  # Light mode, Dark mode colors
            height=10,
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30"),
        )
        self.hide_progress()

        # # Optional: Add space for future buttons in bottom bar
        # self.bottom_left_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        # self.bottom_left_frame.grid(row=1, column=1, padx=(20, 10), pady=5, sticky="w")
        # # Debug label to ensure bottom bar is visible (can be removed later)
        # self.bottom_bar_debug = ctk.CTkLabel(self.bottom_left_frame, text="Bottom Bar", text_color=("black", "white"))
        # self.bottom_bar_debug.grid(row=0, column=0, padx=10, pady=5)

    # ----------------------------------------------HELPER METHODS---------------------------
    def start_move(self, event):
        """Start window drag"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        """Handle window drag"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def minimize_window(self):
        """Custom minimize for overrideredirect window"""
        self._last_geometry = self.geometry()
        self.withdraw()  # Hide current window
        self.minimized_window = ctk.CTkToplevel(self)
        self.minimized_window.overrideredirect(True)
        self.minimized_window.geometry("150x30")
        self.minimized_window.attributes("-topmost", True)
        # Restore button
        restore_button = ctk.CTkButton(
            self.minimized_window,
            text="Restore",
            command=self.restore_window,
            height=30,
            width=150,
        )
        restore_button.pack(fill="both", expand=True)

        # Position minimized window at bottom of screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 200
        y = screen_height - 50

        self.minimized_window.geometry(f"+{x}+{y}")

    def restore_window(self):
        """Restore window from minimized state"""
        if hasattr(self, "_last_geometry"):
            self.geometry(self._last_geometry)
        if hasattr(self, "minimized_window"):
            self.minimized_window.destroy()
        self.deiconify()

    def toggle_maximize(self):
        """Toggle between maximized and normal window"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # If not already maximized, maximize
        if not hasattr(self, "_is_maximized") or not self._is_maximized:
            # Store current geometry before maximizing
            self._original_geometry = self.geometry()

            # Move and resize to full screen
            self.geometry(f"{screen_width}x{screen_height}+0+0")
            self._is_maximized = True
            self.max_button.configure(text="❐")
        else:
            # Restore to previous size
            self.geometry(self._original_geometry)
            self._is_maximized = False
            self.max_button.configure(text="□")

    def update_status(self, message, color=None):
        """Update status in top bar"""
        self.status_label.configure(text=message)
        if color:
            self.status_label.configure(text_color=color)

    def show_help(self):
        """Show help information"""
        help_text = """
            Figma Converter Help:

            1. Token & URL:
            - Paste your Figma access token
            - Enter the Figma file URL

            2. Keyboard Shortcuts:
            - Ctrl+S: Save settings
            - Ctrl+R: Run conversion
            - Ctrl+T: Toggle theme

            3. Features:
            - Auto-save settings
            - Recent conversions list
            - Theme switching
            - Settings export

            Need more help? Visit our documentation.
        """
        dialog = self.show_alert("Help & Information", help_text, "info")

    def apply_button_style(self, button, style="primary"):
        """Apply consistent button styling
        Args:
                button: CTkButton to style
                style: One of 'primary', 'secondary', 'danger'
        """
        styles = {
            "primary": {
                "fg_color": ("green", "dark green"),
                "hover_color": ("dark green", "forest green"),
                "border_width": 2,
                "border_color": ("gray70", "gray30"),
            },
            "secondary": {
                "fg_color": "transparent",
                "hover_color": ("gray75", "gray25"),
                "border_width": 2,
                "border_color": ("gray70", "gray30"),
            },
            "danger": {
                "fg_color": ("red", "dark red"),
                "hover_color": ("dark red", "firebrick"),
                "border_width": 2,
                "border_color": ("gray70", "gray30"),
            },
        }
        button.configure(**styles[style])

    def add_recent_conversion(self, output_path: Path):
        """Add a conversion to recent list"""

        def open_path(path):
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path], check=False)
                else:  # linux
                    subprocess.run(["xdg-open", str(path)], check=False)
            except Exception as e:
                self.out(f"Failed to open path: {e}")
                self.show_alert("Error", f"Could not open file: {e}", "error")

        def open_containing_folder(path):
            try:
                if sys.platform == "win32":
                    subprocess.run(["explorer", "/select,", str(path)], check=False)
                elif sys.platform == "darwin":
                    subprocess.run(["open", "-R", str(path)], check=False)
                else:  # linux
                    subprocess.run(["xdg-open", str(path.parent)], check=False)
            except Exception as e:
                self.out(f"Failed to open containing folder: {e}")
                self.show_alert("Error", f"Could not open folder: {e}", "error")

        def show_context_menu(event, path):
            context_menu = ctk.CTkFrame(self, fg_color=("gray85", "gray20"))

            open_btn = ctk.CTkButton(
                context_menu,
                text="Open File",
                command=lambda: [context_menu.destroy(), open_path(path)],
                height=25,
            )
            open_btn.pack(padx=5, pady=2, fill="x")

            open_folder_btn = ctk.CTkButton(
                context_menu,
                text="Show in Folder",
                command=lambda: [context_menu.destroy(), open_containing_folder(path)],
                height=25,
            )
            open_folder_btn.pack(padx=5, pady=2, fill="x")

            def close_menu(e=None):
                context_menu.destroy()

            # Close menu when clicking outside
            context_menu.bind("<Leave>", lambda e: self.after(1000, close_menu))

            # Position menu at cursor
            context_menu.place(
                x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty()
            )

        self.recent_list.configure(state="normal")
        self.recent_list.insert("1.0", f"➜ {output_path.name}\n")
        self.recent_list.tag_add("link", "1.0", "1.end")
        self.recent_list.tag_config("link", foreground="blue", underline=True)
        self.recent_list.tag_bind(
            "link", "<Button-1>", lambda e, p=output_path: open_path(p)
        )
        self.recent_list.tag_bind(
            "link", "<Button-3>", lambda e, p=output_path: show_context_menu(e, p)
        )

        # Keep only last 5 conversions
        content = self.recent_list.get("1.0", "end")
        if content.count("\n") > 5:
            last_newline = content.find("\n", content.find("\n") + 1)
            self.recent_list.delete("6.0", "end")
        self.recent_list.configure(state="disabled")

    def show_tooltip(self, text):
        """Show tooltip when hovering over elements"""
        self.cancel_tooltip()
        self.tooltip_after_id = self.after(500, lambda: self._create_tooltip(text))

    def _create_tooltip(self, text):
        """Actually create the tooltip"""
        x = self.winfo_pointerx() + 10
        y = self.winfo_pointery() + 10
        self.active_tooltip = ctk.CTkToplevel(self)
        self.active_tooltip.geometry(f"+{x}+{y}")
        self.active_tooltip.wm_overrideredirect(True)
        label = ctk.CTkLabel(
            self.active_tooltip,
            text=text,
            corner_radius=8,
            fg_color=("gray85", "gray20"),
        )
        label.pack(padx=4, pady=4)

    def cancel_tooltip(self):
        """Cancel and destroy any existing tooltip"""
        if self.tooltip_after_id:
            self.after_cancel(self.tooltip_after_id)
            self.tooltip_after_id = None
        if self.active_tooltip:
            self.active_tooltip.destroy()
            self.active_tooltip = None

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            # Collapse sidebar
            self.sidebar_width = 40
            self.sidebar_content.grid_remove()  # Hide content
            self.toggle_button.configure(text="≡")  # Show expand icon
        else:
            # Expand sidebar
            self.sidebar_width = 250
            self.sidebar_content.grid()  # Show content
            self.toggle_button.configure(text="×")  # Show collapse icon

        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar_frame.configure(width=self.sidebar_width)

    def toggle_auto_save(self):
        """- Handle auto save check box changes"""
        state = self.auto_save.get()  # get the boolean state whether true or False
        self.save_button.configure(state="disabled" if state else "normal")
        self.out(
            f"Auto save {'enabled' if state else 'disabled'}"
        )  # we use simple one liners to finish off

    def out(self, message, clear=False):
        """- Helper method to update output textbox
                Args:
                        message: text to display
                        clear: whether to clear previous output
        its convinenet to say out instead of long naming!
        """
        self.output_textbox.configure(state="normal")
        if clear:
            self.output_textbox.delete("0.0", "end")
        self.output_textbox.insert("end", f"{message}\n")
        self.output_textbox.configure(state="disabled")
        self.output_textbox.see("end")  # make sure to show the latest output
        # log every output using logger here
        logging.info(message)

    # alert system modal
    def show_alert(self, title, message, level="info", callback=None):
        """- show a modal alert dialog based on the activity at hand"""
        colors = {
            "info": ("blue", "dark blue"),
            "warning": ("orange", "dark orange"),
            "error": ("red", "dark red"),
        }
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)

        dialog.attributes("-topmost", True)  # make it float on top of main window
        dialog.transient(self)  # make it float on top of main window

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 350) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        msg_label = ctk.CTkLabel(
            dialog, text=message, wraplength=250, font=ctk.CTkFont(size=12)
        )
        msg_label.pack(padx=10, pady=20)

        dialog.deiconify()
        dialog.lift()
        dialog.focus_force()
        # make the background blurred when starting

        # button frame for layout
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        def on_ok():
            if callback:
                try:
                    dialog.destroy()
                    callback()  # execute call back if provided
                except Exception as e:
                    self.out(f"Alert callback error: {e}")
            dialog.destroy()

        # Ok button
        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            command=on_ok,
            fg_color=colors[level][0],
            hover_color=colors[level][1],
            width=100,
        )
        ok_button.pack(side="left", padx=5)

        # cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            border_width=2,
            fg_color=colors[level][0],
            border_color=colors[level][0],
            hover_color=("gray75", "gray75"),
            width=100,
        )
        cancel_button.pack(side="right", padx=5)
        return dialog

    def toggle_theme(self, save_settings=True):
        """Switch between light/dark themes"""
        new_theme = self.theme_var.get()
        ctk.set_appearance_mode(new_theme)
        self.theme_switch.configure(
            text="Dark Mode" if new_theme == "dark" else "Light Mode"
        )
        self.out(f"Theme switched to {new_theme} mode")

        if save_settings and hasattr(self, "token_entry"):
            save_config(
                self.token_entry.get().strip(),
                self.url_entry.get().strip(),
                str(self.auto_save.get()),
                new_theme,
            )
        self.out(f"Theme switched to {new_theme} mode")

    def show_progress(self):
        """Show progress during conversion"""
        self.progress_bar.grid()
        self.progress_bar.set(0)  # reset to start
        self.progress_bar.start()  # speed of animation
        self.update()

    def hide_progress(self):
        """Hide progress after conversion"""
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.update()

    def save_settings(self):
        """Allow the user to manually save the current settings"""
        try:
            token: str = self.token_entry.get().strip()
            url: str = self.url_entry.get().strip()
            auto_save: bool = self.auto_save.get()
            theme: str = self.theme_var.get()

            if (
                not token and not url
            ):  # Changed from checking widget to checking content
                self.show_alert(
                    "Empty Fields", "Nothing to save - both fields are empty", "warning"
                )
                return
            save_config(token, url, auto_save, theme)
            self.out("SUCCESS: Configs saved!")
            self.show_alert("Saved", "Token and url is saved")
        except Exception as e:
            self.out(f"Error while saving settings: {str(e)}")
            self.show_alert(
                "Load Error", f"Error while saving configs{str(e)}", "warning"
            )

    def load_settings(self):
        """Allow the user to load the saved settings"""
        try:
            config = load_config()
            if config:
                # Store original values
                self.original_token = config.get("token", "")
                self.original_url = config.get("url", "")
                self.original_auto_save = str(config.get("auto_save", "True")).lower()
                self.original_theme = config.get("theme", "light")

                # Update UI elements
                self.token_entry.delete(0, "end")
                self.token_entry.insert(0, self.original_token)

                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, self.original_url)

                # Update auto-save and theme
                self.auto_save.set(self.original_auto_save == "true")
                self.theme_var.set(self.original_theme)
                self.toggle_theme(save_settings=False)  # Apply theme without saving

                self.out("Success: Loaded previous config")
                if config.get("last_used"):
                    self.out(f"Info: Settings last saved on {config.get('last_used')}")
        except Exception as e:
            self.out(f"ERROR: Error while loading settings: {str(e)}")
            self.show_alert("Load Error", f"{str(e)}", "warning")

    def clear_settings(self):
        """Clear the settings and revert to original values"""
        self.token_entry.delete(0, "end")
        self.token_entry.insert(0, self.original_token)  # Reset to original token
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, self.original_url)  # Reset to original URL
        self.auto_save.set(self.original_auto_save)  # Reset auto_save
        self.theme_var.set(self.original_theme)  # Reset theme

        save_config("", "")  # Save empty values if needed
        self.out("Settings cleared")

    def export_settings(self):
        """Export current settings to file"""
        try:
            settings = {
                "token": self.token_entry.get(),
                "url": self.url_entry.get(),
                "auto_save": self.auto_save.get(),
                "theme": self.theme_var.get(),
            }

            def continue_export() -> None:
                with open(CONFIG_PATH, "w") as f:
                    json.dump(settings, f, indent=4)
                self.show_alert("Success", "Settings exported successfully!", "info")
                self.out(f"Settings exported to {CONFIG_PATH}")
                self.out(f"Settings exported to {CONFIG_PATH}")

            # Check if essential settings are empty
            if not settings["token"] or not settings["url"]:
                self.show_alert(
                    "Warning",
                    "Some settings are empty. Do you want to export anyway ?",
                    "warning",
                    callback=continue_export,  # pass continuation function
                )
            else:
                continue_export()

        except Exception as e:
            self.show_alert("Error", f"Failed to export settings: {str(e)}", "error")
            self.out(f"Settings export failed: {str(e)}")
            self.out(f"Settings export failed: {str(e)}")

    # -------------------------------------CORE METHODS----------------------------------------
    def convert_design(self):
        """- Handle the design conversion process."""
        # Clear previous output
        self.out("Starting Conversion process ..", clear=True)
        self.update_status("Converting...", ("orange", "dark orange"))
        try:
            # Get input values
            output_path = create_path()
            self.out(f"SUCCESS: Created output directory: {output_path}")
            token = self.token_entry.get().strip()
            url = self.url_entry.get().strip()
            if not token or not url:
                self.out("Error: Please enter both token and URL")
                self.show_alert("Warning", "Please Enter the values", "error")
                return

            file_url = convert_url_to_file_format(url)
            self.out(f"Converted URL format: {file_url}")
            if self.auto_save.get():
                save_config(token, url)
                self.out("Saved configuration for next time.")

            if file_url:
                self.out("Running converter..")
                self.show_progress()
                conversion_thread = Thread(
                    target=self.run_conversion, args=(token, file_url, output_path)
                )
                conversion_thread.daemon = True
                conversion_thread.start()
                self.update_status("Done", ("green", "dark orange"))

            else:
                self.out("Empty url, can't convert empty url")
                self.out("Please check yor url!")
                self.show_alert("Convert Error", f"Try to check your Figma url!")

                self.hide_progress()
                self.update_status("Stopped", ("red", "dark orange"))

        except Exception as e:
            self.out(f"Error while converting Error: {str(e)}")
            self.out(f"Error while converting Error: {str(e)}")

    def run_conversion(self, token, file_url, output_path):
        """- Run conversion in a seprate thead"""
        try:
            converter(token, file_url, output_path)
            # use after() to safely update ui from thread
            self.after(0, lambda: self.out("✓ Conversion completed successfully!"))
            self.after(0, lambda: self.out(f"✓ Output saved to: {output_path}"))
            self.after(0, lambda: self.add_recent_conversion(output_path))
            self.out("Conversion completed successfully!")
        except subprocess.SubprocessError as error:
            self.after(0, lambda: self.out(f"❌ Converter error: {str(error)}"))
            self.out(f"Converter error: {str(error)}")
        finally:
            self.after(0, self.hide_progress)

    def run_check_update(self) -> None:
        """ Run the check for update system on separate thread to prevent blocking"""
        try:
            update_thread = Thread(target=self.check_for_updates)
            update_thread.daemon = True
            update_thread.start()
        except Exception as e:
            self.out(f"There was error running the check update {str(e)}")
        

    def check_for_updates(self):
        """Check for new releases on GitHub"""
        try:
            self.out("Checking for update... ")
            self.show_progress()
            repo_url = f"{self.GITHUB_API_URL}{self.GITHUB_REPO}"
            repo_response: requests.Response   = requests.get(repo_url, timeout=5)

            if repo_response.status_code == 404:
                self.out("Repository not found, skipping update check")
                return

            # If repository exists, check for releases
            releases_url = f"{repo_url}/releases/latest"
            response = requests.get(releases_url, timeout=5)

            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                try:
                    if semver.compare(latest_version, self.CURRENT_VERSION) > 0:
                        self.update_available = True
                        self.show_update_notification(
                            latest_version, release_data["body"], release_data["assets"]
                        )
                except ValueError:
                    self.out("Invalid version format in GitHub release")
            elif response.status_code == 404:
                self.out("No releases found in repository")
            else:
                self.out(f"Failed to check releases: {response.status_code}")
        except requests.RequestException as e:
            self.out(f"Network error checking for updates: {e}")
        except Exception as e:
            self.out(f"Failed to check for updates: {e}")
        finally:
            self.hide_progress()

    def download_and_install_update(self, download_url):
        """Download and install the update"""
        try:
            # Create progress dialog
            progress_dialog = ctk.CTkToplevel(self)
            progress_dialog.title("Downloading Update")
            progress_dialog.geometry("400x150")
            progress_dialog.transient(self)
            progress_dialog.grab_set()

            # Progress label and bar
            progress_label = ctk.CTkLabel(progress_dialog, text="Preparing download...")
            progress_label.pack(pady=10)

            progress_bar = ctk.CTkProgressBar(progress_dialog)
            progress_bar.pack(pady=10, padx=20, fill="x")
            progress_bar.set(0)

            # Download with progress tracking
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get("content-length", 0))

            if response.status_code == 200:
                # Prepare download path
                download_path = self.root / "update.zip"
                block_size = 8192
                downloaded = 0

                with open(download_path, "wb") as f:
                    for data in response.iter_content(block_size):
                        downloaded += len(data)
                        f.write(data)
                        if total_size:
                            progress = downloaded / total_size
                            progress_bar.set(progress)
                            progress_label.configure(
                                text=f"Downloading: {int(progress * 100)}%"
                            )
                            progress_dialog.update()

                progress_label.configure(text="Installing update...")
                progress_bar.set(1)

                # Extract update
                import zipfile

                with zipfile.ZipFile(download_path, "r") as zip_ref:
                    zip_ref.extractall(self.root)

                # Clean up
                download_path.unlink()
                progress_dialog.destroy()

                # Show success message
                self.show_alert(
                    "Update Complete",
                    "The update has been installed successfully. The application will now restart.",
                    "info",
                    self.restart_application,
                )
            else:
                progress_dialog.destroy()
                self.show_alert(
                    "Update Failed",
                    "Failed to download the update. Please try again later.",
                    "error",
                )

        except Exception as e:
            self.out(f"Failed to download/install update: {e}")
            self.show_alert(
                "Update Failed", f"Failed to install the update: {str(e)}", "error"
            )

    def restart_application(self):
        """Restart the application after update"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def show_update_notification(self, latest_version, release_notes="", assets=None):
        """Show update notification to user"""

        def handle_download():
            dialog.destroy()
            if assets and len(assets) > 0:
                download_url = assets[0]["browser_download_url"]
                self.download_and_install_update(download_url)
            else:
                # Fallback to release page if no assets
                open_release_page()

        def open_release_page():
            url = f"https://github.com/{self.GITHUB_REPO}/releases/latest"
            if sys.platform == "win32":
                os.startfile(url)
            elif sys.platform == "darwin":
                subprocess.run(["open", url], check=False)
            else:
                subprocess.run(["xdg-open", url], check=False)
            dialog.destroy()

        dialog = ctk.CTkToplevel(self)
        dialog.title("Update Available")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        msg = f"A new version {latest_version} is available!\nYou are currently using version {self.CURRENT_VERSION}\n\nRelease Notes:\n{release_notes if release_notes else 'No release notes available.'}"
        label = ctk.CTkLabel(dialog, text=msg, wraplength=350)
        label.pack(pady=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        if assets and len(assets) > 0:
            update_btn = ctk.CTkButton(
                btn_frame, text="Download & Install", command=handle_download
            )
        else:
            update_btn = ctk.CTkButton(
                btn_frame, text="View Release Page", command=open_release_page
            )
        update_btn.pack(side="left", padx=5)

        later_btn = ctk.CTkButton(
            btn_frame, text="Remind Later", command=dialog.destroy
        )
        later_btn.pack(side="right", padx=5)


if __name__ == "__main__":
    try:
        app = FigmaConverterApp()
        app.after(500, app.load_settings)
        app.after(2000, app.run_check_update)
        app.mainloop()
    except KeyboardInterrupt:
        print("/ Programm killed by user")
        sys.exit(1)
