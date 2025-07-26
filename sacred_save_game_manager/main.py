import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import os

from .controllers import ConfigManager, GameManager, SaveManager
from .models import GameData


class App:
    SAVE_DIR = "save"
    BACKUP_SAVE_DIR = "save_backup"

    def __init__(self, root):
        self.root = root
        self.root.title("Sacred Gold Path Manager")

        # Initialize managers
        self.config_manager = ConfigManager()
        self.game_manager = GameManager(self.config_manager)
        self.save_manager = SaveManager(self.config_manager)
        
        # Load configuration and initialize UI
        self.config = self.config_manager.load_config()
        self.load_style()

        self.create_main_window()
        self.selected_frame = None

    # === Configuration (delegated to ConfigManager) ===

    def save_config(self):
        """Save current configuration."""
        self.config_manager.save_config(self.config)

    def load_config(self):
        """Load configuration from file."""
        self.config = self.config_manager.load_config()
        return self.config

    # === Custom Styles ===

    def load_style(self):
        self.style = ttk.Style()
        # toolbar buttons
        self.style.configure("Toolbar.TButton", font=("Arial", 10), padding=5)
        self.style.configure("GameFrame.Edit.TButton", font=("Arial", 14), padding=2)
        # game frames
        self.style.configure(
            "GameFrame.Name.TLabel", font=("Arial", 12, "bold"), foreground="#AA5500"
        )
        self.style.configure(
            "GameFrame.Path.TLabel", font=("Arial", 10), foreground="#AA5500"
        )
        # selected frames
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
        return

    # === Main Window UX ===

    def create_main_window(self):
        # notebook
        main_layout = ttk.Frame(self.root)
        main_layout.pack(fill=tk.BOTH, expand=True)
        # games tab
        game_layout = ttk.Frame(main_layout)
        game_layout.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.create_game_tab(parent=game_layout)
        # separator
        separator = ttk.Separator(main_layout, orient="horizontal")
        separator.pack(fill=tk.X)
        # save_dirs tab
        save_layout = ttk.Frame(main_layout)
        save_layout.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.create_save_dirs_tab(parent=save_layout)
        return

    # === Game Tab UX ===

    def create_game_tab(self, parent: ttk.Widget):
        self.create_game_tab_header(parent=parent)
        self.create_game_tab_body(parent=parent)
        return

    def create_game_tab_header(self, parent: ttk.Widget):
        # toolbar
        toolbar = tk.Frame(parent, padx=2, pady=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        # label
        label = tk.Label(toolbar, text="Game Directories", font=("Arial", 14, "bold"))
        label.pack(side=tk.LEFT, padx=2, pady=2)
        # button: remove game
        remove_game_button = ttk.Button(
            toolbar,
            text="Remove",
            command=self.remove_game_handler,
            style="Toolbar.TButton",
        )
        remove_game_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(remove_game_button, "Remove the selected Sacred Gold entry.")
        # button: reset game
        remove_game_button = ttk.Button(
            toolbar,
            text="Reset",
            command=self.reset_game_handler,
            style="Toolbar.TButton",
        )
        remove_game_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(remove_game_button, "Reset to the default save directory.")
        # button: add game
        add_game_button = ttk.Button(
            toolbar, text="Add", command=self.add_game_handler, style="Toolbar.TButton"
        )
        add_game_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(add_game_button, "Add a new Sacred Gold entry.")
        # separator
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill=tk.X)
        return

    def create_game_tab_body(self, parent: ttk.Widget):
        self.game_tab_canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(
            parent, orient=tk.VERTICAL, command=self.game_tab_canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.game_tab_canvas)
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
        self.create_game_tab_games(parent=self.scrollable_frame)
        self.game_tab_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return

    def create_game_tab_games(self, parent: ttk.Widget):
        # Validate all games using GameManager
        self.game_manager.validate_all_games()
        self.config = self.config_manager.get_config()  # Refresh config
        
        for game in self.config["games"]:
            self.create_game_tab_game_frame(parent=parent, game=game)
        return

    def create_game_tab_game_frame(self, parent: ttk.Widget, game: GameData):
        # game frame
        game_frame = ttk.Frame(parent, padding=5, relief=tk.RIDGE, borderwidth=2)
        game_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)
        text = game["name"] if game["valid"] else f"[Invalid] - {game['name']}"
        # name
        name_label = ttk.Label(
            game_frame,
            text=text,
            name="game_name",
            anchor="w",
            style="GameFrame.Name.TLabel",
        )
        name_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        # save directory
        save_dir_label = ttk.Label(
            game_frame, text="Save Directory:", name="save_dir_label"
        )
        save_dir_label.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        save_dir_path = ttk.Label(
            game_frame,
            text=self.game_manager.get_game_symlink_target(game=game),
            name="save_dir_path",
            style="GameFrame.Path.TLabel",
        )
        save_dir_path.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        # handlers
        if game["valid"]:
            self._add_selection_handler(widget=game_frame, frame=game_frame, game=game)
        else:
            self._add_hover_handler(widget=game_frame, frame=game_frame, game=game)
        self._add_scroll_handler(widget=game_frame)
        return

    def _add_selection_handler(
        self, widget: ttk.Widget, frame: ttk.Widget, game: GameData
    ):
        widget.bind(
            "<Button-1>", lambda event, f2=frame, f3=game: self.select_frame(f2, f3)
        )
        for child in widget.winfo_children():
            self._add_selection_handler(widget=child, frame=frame, game=game)
        return

    def _add_hover_handler(self, widget: ttk.Widget, frame: ttk.Widget, game: GameData):
        hover_message = (
            "To use this game, restart the application after making sure that the game directory is valid:\n"
            f"- Either the game path does not contain any entry named '{App.SAVE_DIR}', or '{App.SAVE_DIR}' is a directory or symlink to a directory;\n"
            f"- Either the game path does not contain any entry named '{App.BACKUP_SAVE_DIR}', or '{App.BACKUP_SAVE_DIR}' is a directory;\n"
            f"- '{App.SAVE_DIR}' cannot be a non-empty directory when '{App.BACKUP_SAVE_DIR}' already exists."
        )
        if not hasattr(self, "_active_hover_box"):
            self._active_hover_box = None

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
        return

    def select_frame(self, frame: ttk.Frame, game: GameData):
        # clear previously selected frame
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
            # select frame
            frame.config(style="Selected.TFrame")
            for widget in frame.winfo_children():
                if isinstance(widget, ttk.Label):
                    if widget.winfo_name() == "game_name":
                        widget.config(style="Selected.GameFrame.Name.TLabel")
                    elif widget.winfo_name() == "save_dir_path":
                        widget.config(style="Selected.GameFrame.Path.TLabel")
                    else:
                        widget.config(style="Selected.TLabel")
            # update selected frame
            self.selected_frame = (frame, game)
        else:
            self.selected_frame = None
        return

    def _add_scroll_handler(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows and macOS
        widget.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        widget.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        for child in widget.winfo_children():
            self._add_scroll_handler(child)
        return

    def _on_mousewheel(self, event):
        if event.num == 4 or event.num == 5:
            delta = -1 if event.num == 5 else 1
        else:
            delta = event.delta // 120
        self.game_tab_canvas.yview_scroll(-delta, "units")
        return

    # === Game Tab Handlers ===

    def add_game_handler(self) -> None:
        selected_path = filedialog.askdirectory(title="Select Sacred Gold installation")
        if selected_path:
            # Use GameManager for validation
            if not self.game_manager.is_valid_game_directory(selected_path):
                if os.path.islink(selected_path):
                    messagebox.showerror(
                        "Invalid Directory", "Symbolic links are not supported."
                    )
                elif not os.path.isdir(selected_path):
                    messagebox.showerror(
                        "Invalid Directory", "Selected path is not a directory."
                    )
                else:
                    messagebox.showerror(
                        "Invalid Directory", "Sacred.exe not found in selected directory."
                    )
                return
            
            # Check if game already exists
            for game in self.config["games"]:
                if game["path"] == selected_path:
                    messagebox.showinfo(
                        "Game already added",
                        f"This directory has already been added as '{game['name']}'.",
                    )
                    return

            name = simpledialog.askstring(
                "Name", "Provide a name for this Sacred Gold installation:"
            )
            if not name:
                name = "Sacred Gold"
            
            game = {"name": name, "path": selected_path}
            game = self.game_manager.validate_game_directory(game=game)
            if game["valid"]:
                self.create_game_tab_game_frame(parent=self.scrollable_frame, game=game)
                self.config_manager.add_game(game)
                self.config = self.config_manager.get_config()  # Refresh config
        return

    def reset_game_handler(self):
        if self.selected_frame:
            frame, game = self.selected_frame
            game = self.game_manager.validate_game_directory(game=game)
            if game["valid"] and self.game_manager.rebind_symlink(
                link=pathlib.Path(game["save"]),
                target=pathlib.Path(game["save_backup"]),
            ):
                save_dir_path = frame.nametowidget("save_dir_path")
                if save_dir_path:
                    save_dir_path.config(text="default")
        else:
            messagebox.showinfo(
                "No Game Selected", "Please select a Sacred Gold entry to reset."
            )

    def remove_game_handler(self) -> None:
        if self.selected_frame:
            frame, game = self.selected_frame
            # Fix the bug: use 'name' instead of 'Bottlename'
            if messagebox.askyesno(
                "Remove Game",
                f"Are you sure you want to remove '{game['name']}'?",
            ):
                self.selected_frame = None
                frame.destroy()
                self.config_manager.remove_game(game)
                self.config = self.config_manager.get_config()  # Refresh config
        else:
            messagebox.showinfo(
                "No Game Selected", "Please select a Sacred Gold entry to remove."
            )
        return

    # === Save Dirs Tab UX ===

    def create_save_dirs_tab(self, parent: ttk.Widget):
        self.create_save_dirs_tab_header(parent=parent)
        self.create_save_dirs_tab_body(parent=parent)
        return

    def create_save_dirs_tab_header(self, parent: ttk.Widget):
        # toolbar
        toolbar = tk.Frame(parent, padx=2, pady=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        # label
        label = tk.Label(toolbar, text="Save Directories", font=("Arial", 14, "bold"))
        label.pack(side=tk.LEFT, padx=2, pady=2)
        # button: remove save dirs
        remove_game_button = ttk.Button(
            toolbar,
            text="Remove",
            command=self.remove_save_dir_handler,
            style="Toolbar.TButton",
        )
        remove_game_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(remove_game_button, "Remove one or more save directories.")
        # button: add save dirs
        add_game_button = ttk.Button(
            toolbar,
            text="Add",
            command=self.add_save_dir_handler,
            style="Toolbar.TButton",
        )
        add_game_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.add_tooltip(add_game_button, "Add one or more save directories.")
        # separator
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill=tk.X)
        return

    def create_save_dirs_tab_body(self, parent: ttk.Widget):
        # search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        # label
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)
        # search bar
        search_var = tk.StringVar()
        search_bar = ttk.Entry(search_frame, textvariable=search_var)
        search_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # search icon
        search_icon = ttk.Label(search_frame, text="🔍")
        search_icon.pack(side=tk.RIGHT, padx=5)
        # listbox
        listbox = tk.Listbox(
            parent,
            height=10,
            exportselection=False,
            selectmode=tk.EXTENDED,
            name="save_dirs_listbox",
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # listbox content
        self.refresh_listbox(listbox=listbox)
        # footer frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        # override button
        override_game_button = ttk.Button(
            button_frame, text="Override", state=tk.DISABLED, style="Toolbar.TButton"
        )
        override_game_button.pack(side=tk.RIGHT, padx=5)
        self.add_tooltip(
            override_game_button,
            "Overrides the save directory of the currently selected game.",
        )

        # listbox: filter based on changes in the search bar
        def update_list(*args):
            override_game_button.config(state=tk.DISABLED)
            listbox.delete(0, tk.END)
            for path in self.config["save_dirs"]:
                if search_var.get().lower() in path.lower():
                    listbox.insert(tk.END, path)

        search_var.trace("w", update_list)

        # enable/disable button automatically
        def on_select(event):
            if len(listbox.curselection()) == 1:
                override_game_button.config(state=tk.NORMAL)
            else:
                override_game_button.config(state=tk.DISABLED)

        listbox.bind("<<ListboxSelect>>", on_select)
        # override game save dir
        override_game_button.config(
            command=lambda: self.override_save_dir_handler(listbox=listbox)
        )
        return

    def refresh_listbox(self, listbox: tk.Listbox):
        paths = self.config["save_dirs"]
        listbox.delete(0, tk.END)
        for path in paths:
            listbox.insert(tk.END, path)
        return

    # === Save Dir Tab Handlers ===

    def add_save_dir_handler(self):
        selected_path = filedialog.askdirectory(title="Select save archive.")
        listbox = self.root.nametowidget("!frame.!frame2.save_dirs_listbox")
        if selected_path and listbox:
            add_recursively = messagebox.askyesno(
                "Add recursively",
                f"Do you want to recursively add every terminal directories contained in {selected_path}?",
            )
            
            # Use SaveManager to add directories
            new_dirs = self.save_manager.add_save_directory(selected_path, recursive=add_recursively)
            
            # Update UI
            for new_dir in new_dirs:
                listbox.insert(tk.END, new_dir)
            
            # Refresh config
            self.config = self.config_manager.get_config()
        return

    def remove_save_dir_handler(self):
        listbox = self.root.nametowidget("!frame.!frame2.save_dirs_listbox")
        if listbox:
            selected = listbox.curselection()
            if selected:
                confirm = messagebox.askyesno(
                    "Confirm Removal",
                    f"Are you sure you want to remove {len(selected)} selected directory(ies)?",
                )
                if not confirm:
                    return
                
                # Get paths to remove
                paths_to_remove = []
                for index in reversed(selected):
                    path = listbox.get(index)
                    paths_to_remove.append(path)
                    listbox.delete(index)
                
                # Use SaveManager to remove directories
                self.save_manager.remove_save_directories(paths_to_remove)
                
                # Refresh config
                self.config = self.config_manager.get_config()
        return

    def override_save_dir_handler(self, listbox: tk.Listbox):
        # get target save dir
        selected = listbox.curselection()
        assert len(selected) == 1
        target = pathlib.Path(listbox.get(selected[0]))
        
        # Use SaveManager to validate directory
        if not self.save_manager.validate_save_directory(str(target)):
            messagebox.showerror("Invalid Path", f"{target} is not a directory.")
            listbox.select_clear()
            return
        
        # override
        if self.selected_frame:
            frame, game = self.selected_frame
            game = self.game_manager.validate_game_directory(game=game)
            if game["valid"] and self.game_manager.rebind_symlink(
                link=pathlib.Path(game["save"]), target=pathlib.Path(target)
            ):
                save_dir_path = frame.nametowidget("save_dir_path")
                if save_dir_path:
                    save_dir_path.config(text=str(target))
        else:
            messagebox.showinfo("No Game Selected", "Please select a game first.")
        return

    # === Helpers UX ===

    def add_tooltip(self, widget, text):
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
        return


if __name__ == "__main__":
    root = tk.Tk()
    root.minsize(800, 700)
    app = App(root)
    root.mainloop()
