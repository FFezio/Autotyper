import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

class ConfigLoader:
    @dataclass
    class ConfigFile:
        browser_path: str = ""
        typing_delay: float = 120.0
        first_time: bool = True

    _CONFIG_FILE_PATH:Path = Path("config.conf")
    _loaded_file:Optional[ConfigFile] = None

    @classmethod
    def create_default_template(cls):
        """
        Creates a default config file
        :return:
        """
        with open(cls._CONFIG_FILE_PATH, "w") as file:
            default_config_file = cls.ConfigFile()
            file.write(json.dumps(asdict(default_config_file), indent=2))


    @classmethod
    def update(cls, config_file:ConfigFile):
        """
        Updates the config file
        :param config_file: The config file data to update.
        :return:
        """
        with open(cls._CONFIG_FILE_PATH,"w") as file:
            file.write(json.dumps(asdict(config_file), indent=2))

    @classmethod
    def load(cls, force:bool=False) -> ConfigFile:
        """
        Loads the config file if is not already loaded.(if exists, else a new one will be created).
        If force is enabled it will reload the file.
        :param force: Reloads the file if it's already loaded.
        :return:
        """
        if not cls._CONFIG_FILE_PATH.is_file():
            cls.create_default_template()

        if cls._loaded_file and not force:
            return cls._loaded_file

        with open(cls._CONFIG_FILE_PATH, "r") as file:
            file_data = file.read()
            if not file_data:
                cls.create_default_template()
                return cls._loaded_file
            cls._loaded_file = cls.ConfigFile(**json.loads(file_data))
            return cls._loaded_file

