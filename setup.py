from setuptools import setup, find_packages

setup(
    name="sacred-save-game-manager",
    version="1.0.0",
    author="Patroclo Picchiaduro",
    author_email="patroclo.picchiaduro.25@gmail.com",
    description="A save game manager for Sacred",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/PatrocloPicchiaduro/SacredSaveGameManager",
    packages=find_packages(include=["sacred_save_game_manager", "sacred_save_game_manager.*"]),
    install_requires=[
        "Pygments==2.19.1",
        "rich==13.9.4",
    ],
    python_requires=">=3.13",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "sacred-save-game-manager=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
