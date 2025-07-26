"""UI management for Sacred Save Game Manager."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from .config_manager import ConfigManager
from .game_manager import GameManager
from .save_manager import SaveManager
from ..models import GameData


class UIManager:
    """Handles UI components, styling, and layout management."""
    
    def __init__(self, root: tk.Tk, config_manager: ConfigManager, 
                 game_manager: GameManager, save_manager: SaveManager):
        self.root = root
        self.config_manager = config_manager
        self.game_manager = game_manager
        self.save_manager = save_manager
        
        # UI state
        self.selected_frame: Optional[tuple] = None
        self._active_hover_box: Optional[tk.Toplevel] = None
        
        # UI components (will be set during creation)
        self.game_tab_canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[ttk.Frame] = None
        self.style: Optional[ttk.Style] = None
        
        # Event handlers (to be set by App)
        self.add_game_handler: Optional[Callable] = None
        self.remove_game_handler: Optional[Callable] = None
        self.reset_game_handler: Optional[Callable] = None
        self.add_save_dir_handler: Optional[Callable] = None
        self.remove_save_dir_handler: Optional[Callable] = None
        self.override_save_dir_handler: Optional[Callable] = None
    
    def setup_main_window(self) -> None:
        """Initialize the main window with title and minimum size."""
        self.root.title("Sacred Gold Path Manager")
        self.root.minsize(800, 700)
        self.create_styles()
        self.create_main_layout()
    
    def create_styles(self) -> None:
        """Configure all ttk styles for the application."""
        self.style = ttk.Style()
        
        # Toolbar buttons
        self.style.configure("Toolbar.TButton", font=("Arial", 10), padding=5)
        self.style.configure("GameFrame.Edit.TButton", font=("Arial", 14), padding=2)
        
        # Game frames
        self.style.configure(
            "GameFrame.Name.TLabel", font=("Arial", 12, "bold"), foreground="#AA5500"
        )
        self.style.configure(
            "GameFrame.Path.TLabel", font=("Arial", 10), foreground="#AA5500"
        )
        
        # Selected frames
        self.style.configure(
            "Selected.TFrame", background="#A9A9A9", relief="solid", borderwidth=3
        )
        self.style.configure("Selected.TLabel", background="#A9A9A9")
        self.style.configure(
            "Selected.GameFrame.Name.TLabel",
            background="#A9A9A9",
            font=("Arial", 12, "bold"),
            foreground="#AA5500",
        )
        self.style.configure(
            "Selected.GameFrame.Path.TLabel",
            background="#A9A9A9",
            font=("Arial", 10),
            foreground="#AA5500",
        )
        self.style.configure("Selected.TButton", background="#A9A9A9")
        self.style.configure(
            "Selected.GameFrame.Edit.TButton",
            background="#A9A9A9",
            font=("Arial", 14),
            padding=2,
        )
    
    def create_main_layout(self) -> None:
        """Create the main window layout with game and save directory sections."""
        # Main container
        main_layout = ttk.Frame(self.root)
        main_layout.pack(fill=tk.BOTH, expand=True)
        
        # Games section (top)
        game_layout = ttk.Frame(main_layout)
        game_layout.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.create_game_tab(parent=game_layout)
        
        # Separator
        separator = ttk.Separator(main_layout, orient="horizontal")
        separator.pack(fill=tk.X)
        
        # Save directories section (bottom)
        save_layout = ttk.Frame(main_layout)
        save_layout.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.create_save_dirs_tab(parent=save_layout)
    
    def create_game_tab(self, parent: ttk.Widget) -> None:
        """Create the game directories tab."""
        self.create_game_tab_header(parent=parent)
        self.create_game_tab_body(parent=parent)
    
    def create_game_tab_header(self, parent: ttk.Widget) -> None:
        """Create the game tab header with toolbar buttons."""
        # Toolbar
        toolbar = tk.Frame(parent, padx=2, pady=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Label
        label = tk.Label(toolbar, text="Game Directories", font=("Arial", 14, "bold"))
        label.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Remove button
        remove_button = ttk.Button(
            toolbar,
            text="Remove",
            command=self.remove_game_handler,
            style="Toolbar.TButton",
        )
        remove_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(remove_button, "Remove the selected Sacred Gold entry.")
        
        # Reset button
        reset_button = ttk.Button(
            toolbar,
            text="Reset",
            command=self.reset_game_handler,
            style="Toolbar.TButton",
        )
        reset_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(reset_button, "Reset to the default save directory.")
        
        # Add button
        add_button = ttk.Button(
            toolbar, 
            text="Add", 
            command=self.add_game_handler, 
            style="Toolbar.TButton"
        )
        add_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(add_button, "Add a new Sacred Gold entry.")
        
        # Separator
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill=tk.X)
    
    def create_game_tab_body(self, parent: ttk.Widget) -> None:
        """Create the scrollable game list body."""
        self.game_tab_canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(
            parent, orient=tk.VERTICAL, command=self.game_tab_canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.game_tab_canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.game_tab_canvas.configure(
                scrollregion=self.game_tab_canvas.bbox("all")
            ),
        )
        
        window_id = self.game_tab_canvas.create_window(
            (5, 5), window=self.scrollable_frame, anchor="nw"
        )
        
        def resize_scrollable_frame(event):
            self.game_tab_canvas.itemconfig(window_id, width=event.width - 10)
        
        self.game_tab_canvas.bind("<Configure>", resize_scrollable_frame)
        self.game_tab_canvas.configure(yscrollcommand=scrollbar.set)
        self._add_scroll_handler(self.game_tab_canvas)
        
        # Pack components
        self.game_tab_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_save_dirs_tab(self, parent: ttk.Widget) -> None:
        """Create the save directories tab."""
        self.create_save_dirs_tab_header(parent=parent)
        self.create_save_dirs_tab_body(parent=parent)
    
    def create_save_dirs_tab_header(self, parent: ttk.Widget) -> None:
        """Create the save directories tab header."""
        # Toolbar
        toolbar = tk.Frame(parent, padx=2, pady=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Label
        label = tk.Label(toolbar, text="Save Directories", font=("Arial", 14, "bold"))
        label.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Remove button
        remove_button = ttk.Button(
            toolbar,
            text="Remove",
            command=self.remove_save_dir_handler,
            style="Toolbar.TButton",
        )
        remove_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(remove_button, "Remove one or more save directories.")
        
        # Add button
        add_button = ttk.Button(
            toolbar,
            text="Add",
            command=self.add_save_dir_handler,
            style="Toolbar.TButton",
        )
        add_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(add_button, "Add one or more save directories.")
        
        # Separator
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill=tk.X)
    
    def create_save_dirs_tab_body(self, parent: ttk.Widget) -> None:
        """Create the save directories tab body with search and list."""
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Search label
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)
        
        # Search bar
        search_var = tk.StringVar()
        search_bar = ttk.Entry(search_frame, textvariable=search_var)
        search_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Search icon
        search_icon = ttk.Label(search_frame, text="🔍")
        search_icon.pack(side=tk.RIGHT, padx=5)
        
        # Listbox
        listbox = tk.Listbox(
            parent,
            height=10,
            exportselection=False,
            selectmode=tk.EXTENDED,
            name="save_dirs_listbox",
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Footer frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Override button
        override_button = ttk.Button(
            button_frame, text="Override", state=tk.DISABLED, style="Toolbar.TButton"
        )
        override_button.pack(side=tk.RIGHT, padx=5)
        self.add_tooltip(
            override_button,
            "Overrides the save directory of the currently selected game.",
        )
        
        # Configure search functionality
        def update_list(*args):
            override_button.config(state=tk.DISABLED)
            listbox.delete(0, tk.END)
            config = self.config_manager.get_config()
            for path in config["save_dirs"]:
                if search_var.get().lower() in path.lower():
                    listbox.insert(tk.END, path)
        
        search_var.trace("w", update_list)
        
        # Configure selection handling
        def on_select(event):
            if len(listbox.curselection()) == 1:
                override_button.config(state=tk.NORMAL)
            else:
                override_button.config(state=tk.DISABLED)
        
        listbox.bind("<<ListboxSelect>>", on_select)
        
        # Configure override button
        override_button.config(
            command=lambda: self.override_save_dir_handler(listbox=listbox)
        )
    
    def add_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Add a tooltip to a widget."""
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        tooltip_label = ttk.Label(
            tooltip, text=text, background="white", relief=tk.SOLID, padding=3
        )
        tooltip_label.pack()
        
        def on_enter(event):
            tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip.deiconify()
        
        def on_leave(event):
            tooltip.withdraw()
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _add_scroll_handler(self, widget: tk.Widget) -> None:
        """Add mouse wheel scroll handling to a widget and its children."""
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows and macOS
        widget.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        widget.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        for child in widget.winfo_children():
            self._add_scroll_handler(child)
    
    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling."""
        if self.game_tab_canvas:
            if event.num == 4 or event.num == 5:
                delta = -1 if event.num == 5 else 1
            else:
                delta = event.delta // 120
            self.game_tab_canvas.yview_scroll(-delta, "units")
    
    def refresh_listbox(self, listbox: tk.Listbox) -> None:
        """Refresh the save directories listbox."""
        config = self.config_manager.get_config()
        paths = config["save_dirs"]
        listbox.delete(0, tk.END)
        for path in paths:
            listbox.insert(tk.END, path)
    
    def populate_games(self) -> None:
        """Populate the games list with current configuration."""
        if not self.scrollable_frame:
            return
            
        # Clear existing games
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Validate all games and refresh
        self.game_manager.validate_all_games()
        config = self.config_manager.get_config()
        
        # Create game frames
        for game in config["games"]:
            self.create_game_frame(parent=self.scrollable_frame, game=game)
    
    def create_game_frame(self, parent: ttk.Widget, game: GameData) -> None:
        """Create a game frame for display in the games list."""
        # Game frame
        game_frame = ttk.Frame(parent, padding=5, relief=tk.RIDGE, borderwidth=2)
        game_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)
        text = game["name"] if game["valid"] else f"[Invalid] - {game['name']}"
        
        # Name label
        name_label = ttk.Label(
            game_frame,
            text=text,
            name="game_name",
            anchor="w",
            style="GameFrame.Name.TLabel",
        )
        name_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Save directory label
        save_dir_label = ttk.Label(
            game_frame, text="Save Directory:", name="save_dir_label"
        )
        save_dir_label.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Save directory path
        save_dir_path = ttk.Label(
            game_frame,
            text=self.game_manager.get_game_symlink_target(game=game),
            name="save_dir_path",
            style="GameFrame.Path.TLabel",
        )
        save_dir_path.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Add event handlers
        if game["valid"]:
            self._add_selection_handler(widget=game_frame, frame=game_frame, game=game)
        else:
            self._add_hover_handler(widget=game_frame, frame=game_frame, game=game)
        self._add_scroll_handler(widget=game_frame)
    
    def _add_selection_handler(self, widget: tk.Widget, frame: ttk.Widget, game: GameData) -> None:
        """Add selection event handlers to a widget and its children."""
        widget.bind(
            "<Button-1>", lambda event, f2=frame, f3=game: self.select_frame(f2, f3)
        )
        for child in widget.winfo_children():
            self._add_selection_handler(widget=child, frame=frame, game=game)
    
    def _add_hover_handler(self, widget: tk.Widget, frame: ttk.Widget, game: GameData) -> None:
        """Add hover tooltip for invalid games."""
        hover_message = (
            "To use this game, restart the application after making sure that the game directory is valid:\n"
            f"- Either the game path does not contain any entry named 'save', or 'save' is a directory or symlink to a directory;\n"
            f"- Either the game path does not contain any entry named 'save_backup', or 'save_backup' is a directory;\n"
            f"- 'save' cannot be a non-empty directory when 'save_backup' already exists."
        )
        
        def on_enter(event):
            if self._active_hover_box is not None:
                self._active_hover_box.destroy()
            
            hover_box = tk.Toplevel(self.root)
            hover_box.wm_overrideredirect(True)
            hover_box.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = ttk.Label(
                hover_box,
                text=hover_message,
                background="yellow",
                relief="solid",
                borderwidth=1,
                padding=5,
            )
            label.pack()
            self._active_hover_box = hover_box
        
        def on_leave(event):
            if self._active_hover_box is not None:
                self._active_hover_box.destroy()
                self._active_hover_box = None
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        for child in widget.winfo_children():
            self._add_hover_handler(widget=child, frame=frame, game=game)
    
    def select_frame(self, frame: ttk.Frame, game: GameData) -> None:
        """Handle frame selection for games."""
        # Clear previously selected frame
        if self.selected_frame:
            prev = self.selected_frame[0]
            prev.config(style="TFrame")
            for widget in prev.winfo_children():
                if isinstance(widget, ttk.Label):
                    if widget.winfo_name() == "game_name":
                        widget.config(style="GameFrame.Name.TLabel")
                    elif widget.winfo_name() == "save_dir_path":
                        widget.config(style="GameFrame.Path.TLabel")
                    else:
                        widget.config(style="TLabel")
        
        if self.selected_frame != (frame, game):
            # Select frame
            frame.config(style="Selected.TFrame")
            for widget in frame.winfo_children():
                if isinstance(widget, ttk.Label):
                    if widget.winfo_name() == "game_name":
                        widget.config(style="Selected.GameFrame.Name.TLabel")
                    elif widget.winfo_name() == "save_dir_path":
                        widget.config(style="Selected.GameFrame.Path.TLabel")
                    else:
                        widget.config(style="Selected.TLabel")
            # Update selected frame
            self.selected_frame = (frame, game)
        else:
            self.selected_frame = None
