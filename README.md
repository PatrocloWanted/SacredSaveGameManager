# SacredSaveGameManager

**SacredSaveGameManager** is a Python application built with Tkinter for managing game directories and save files for the game "Sacred Gold".

## Features
- **Game Directory Management:** Add, remove, and reset game directories.
- **Save Directory Management:** Add and remove save directories.
- **One-Click links:** Link games with any save directory.
- **Persistence:** Configuration is saved in `config.json`.

## Installation
1. Clone the repository:

```bash
git clone <repository-url>
cd SacredSaveGameManager
```

2. Install dependencies:

```
pip install -r requirements.txt
```

#### With Conda Setup

You can set up a **conda** environment for this project once as follows:

```bash
conda create --name=py313 python=3.13
conda activate py313
pip install -r requirements.txt
```

## Usage
Run the application using Python 3.13 or later:


```css
python3 sacred_save_game_manager/main.py
```

#### With Conda Setup


Activate the environment first:

```bash
conda activate py313
python3 sacred_save_game_manager/main.py
```


## Configuration
- Config File: config.json stores game and save directory configurations.

## Dependencies

The project requires `python 3.13`, and:
- Pygments==2.19.1
- rich==13.9.4


## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

# Note:
- Ensure Python 3.13 or later is installed and accessible.
- Customize setup.py for any additional configurations or styling changes.
