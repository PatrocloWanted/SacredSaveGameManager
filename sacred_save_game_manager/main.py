import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import os
from typing import NotRequired, TypedDict


GameData = TypedDict(
    "GameData",
    {
        "name": str,
        "path": str,
        "save": NotRequired[str],
        "save_backup": NotRequired[str],
        "valid": NotRequired[bool],
    },
)


class App:
    CONFIG_FILE = (
        "sacred_save_game_manager/config.json"
        if pathlib.Path("sacred_save_game_manager").is_dir()
        else "config.json"
    )
    SAVE_DIR = "save"
    BACKUP_SAVE_DIR = "save_backup"

    def __init__(self, root):
        self.root = root
        self.root.title("Sacred Gold Path Manager")

        self.config = self.load_config()
        self.load_style()

        self.create_main_window()
        self.selected_frame = None

    # === Configuration ===

    def save_config(self):
        self.config["save_dirs"].sort()
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)
        return

    def load_config(self):
        if not os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "w") as f:
                json.dump({"games": [], "save_dirs": []}, f, indent=4)
        with open(self.CONFIG_FILE, "r") as f:
            config = json.load(f)
            config["save_dirs"].sort()
            return config

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
        self.config["games"] = [
            self.validate_game_directory(game=game) for game in self.config["games"]
        ]
        self.save_config()
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
            text=self.get_game_symlink_target(game=game),
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

    def get_game_symlink_target(self, game: GameData):
        game = self.validate_game_directory(game=game)
        if game["valid"]:
            target_path = pathlib.Path(game["save"]).resolve()
            if target_path == pathlib.Path(game["save_backup"]):
                return "default"
            else:
                return str(target_path)
        else:
            return "invalid"

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
            if os.path.islink(selected_path):
                messagebox.showerror(
                    "Invalid Directory", "Symbolic links are not supported."
                )
                return
            if not os.path.isdir(selected_path):
                messagebox.showerror(
                    "Invalid Directory", "Selected path is not a directory."
                )
                return
            if not os.path.isfile(os.path.join(selected_path, "Sacred.exe")):
                messagebox.showerror(
                    "Invalid Directory", "Sacred.exe not found in selected directory."
                )
                return
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
            game = self.validate_game_directory(game=game)
            if game["valid"]:
                self.create_game_tab_game_frame(parent=self.scrollable_frame, game=game)
                self.config["games"].append(game)
                self.save_config()
        return

    def validate_game_directory(self, game: GameData) -> GameData:
        game["valid"] = False
        save_dir = self._match_target_in_directory(
            directory=game["path"], target=App.SAVE_DIR, case_insensitive=True
        ) or pathlib.Path(game["path"], App.SAVE_DIR)
        backup_save_dir = self._match_target_in_directory(
            directory=game["path"], target=App.BACKUP_SAVE_DIR, case_insensitive=True
        ) or pathlib.Path(game["path"], App.BACKUP_SAVE_DIR)
        # The save directory either does not exist or it is a directory/symlink to a directory.
        if save_dir.exists(follow_symlinks=False):
            if not save_dir.is_symlink() and not save_dir.is_dir(follow_symlinks=True):
                messagebox.showerror(
                    "Unexpected Error", f"{save_dir} is not a directory."
                )
                return game
        # The backup save directory either does not exist or it is a directory.
        if backup_save_dir.exists(follow_symlinks=False) and not backup_save_dir.is_dir(
            follow_symlinks=False
        ):
            messagebox.showerror(
                "Unexpected Error", f"{backup_save_dir} is not a directory."
            )
            return game
        # Fail when there already is a backup save directory and the save directory is a non-empty directory.
        if (
            backup_save_dir.exists(follow_symlinks=False)
            and save_dir.exists(follow_symlinks=False)
            and save_dir.is_dir(follow_symlinks=False)
        ):
            if len(list(save_dir.iterdir())) > 0:
                messagebox.showerror("Unexpected Error", f"{save_dir} is not empty.")
                return game
            else:
                # Remove the save directory, so that it can be replaced by a symlink.
                save_dir.rmdir()
        # Create the backup save directory when it does not exist. Transfer content of save directory when it is not a symlink.
        if not backup_save_dir.exists(follow_symlinks=False):
            if not save_dir.exists(follow_symlinks=False) or save_dir.is_symlink():
                backup_save_dir.mkdir(parents=False, exist_ok=True)
            else:
                save_dir.replace(target=backup_save_dir)
        # Create the save directory symlink when it does not exist.
        if not save_dir.exists(follow_symlinks=False):
            save_dir.symlink_to(target=backup_save_dir, target_is_directory=True)
        # Update & return
        game["save"] = str(save_dir)
        game["save_backup"] = str(backup_save_dir)
        game["valid"] = True
        return game

    def _match_target_in_directory(
        self, directory: str, target: str, case_insensitive: bool = True
    ) -> pathlib.Path | None:
        target = target.casefold() if case_insensitive else target
        for item in pathlib.Path(directory).rglob("*"):
            if (case_insensitive and item.name.casefold() == target) or (
                not case_insensitive and item.name == target
            ):
                return item
        return None

    def reset_game_handler(self):
        if self.selected_frame:
            frame, game = self.selected_frame
            game = self.validate_game_directory(game=game)
            if game["valid"] and self.rebind_symlink(
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

    def rebind_symlink(self, link: pathlib.Path, target: pathlib.Path) -> bool:
        assert target.exists(follow_symlinks=False) and target.is_dir()
        try:
            if link.exists(follow_symlinks=False):
                assert link.is_symlink()
                link.unlink(missing_ok=True)
            link.symlink_to(target=target, target_is_directory=True)
            return True
        except OSError as e:
            messagebox.showerror("Error", f"Failed to rebind symlink: {e}")
        return False

    def remove_game_handler(self) -> None:
        if self.selected_frame:
            frame, game = self.selected_frame
            if messagebox.askyesno(
                "Remove Game",
                f"Are you sure you want to remove '{game['Bottlename']}'?",
            ):
                self.selected_frame = None
                frame.destroy()
                self.config["games"].remove(game)
                self.save_config()
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
            if add_recursively:
                for root, dirs, _ in os.walk(selected_path):
                    if not dirs:
                        if root not in self.config["save_dirs"]:
                            self.config["save_dirs"].append(root)
                            listbox.insert(tk.END, root)
            elif selected_path not in self.config["save_dirs"]:
                self.config["save_dirs"].append(selected_path)
                listbox.insert(tk.END, selected_path)
            self.save_config()
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
                for index in reversed(selected):
                    path = listbox.get(index)
                    if path in self.config["save_dirs"]:
                        self.config["save_dirs"].remove(path)
                    listbox.delete(index)
                self.save_config()
        return

    def override_save_dir_handler(self, listbox: tk.Listbox):
        # get target save dir
        selected = listbox.curselection()
        assert len(selected) == 1
        target = pathlib.Path(listbox.get(selected[0]))
        if not target.exists(follow_symlinks=False) or not target.is_dir():
            messagebox.showerror("Invalid Path", f"{target} is not a directory.")
            listbox.select_clear()
            return
        # override
        if self.selected_frame:
            frame, game = self.selected_frame
            game = self.validate_game_directory(game=game)
            if game["valid"] and self.rebind_symlink(
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
