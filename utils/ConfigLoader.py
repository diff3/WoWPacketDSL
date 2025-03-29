#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml


class ConfigLoader:
    _config = None 

    @staticmethod
    def get(key:str, default:str=None) -> dict:
        """
        Retrieves a value from the loaded configuration.
        """

        if ConfigLoader._config is None:
            raise RuntimeError("Configuration has not been loaded.")
        
        return ConfigLoader._config.get(key, default)

    @staticmethod
    def load_config(filepath:str = "etc/config.yaml") -> dict:
        """
        Loads the configuration file if not already cached.
        """

        if ConfigLoader._config is None:
            try:
                with open(filepath, 'r') as file:
                    ConfigLoader._config = yaml.safe_load(file)
            except FileNotFoundError:
                raise RuntimeError(f"Configuration file not found at {filepath}.")
            except yaml.YAMLError as e:
                raise RuntimeError(f"Error parsing YAML file: {e}")
        
        return ConfigLoader._config