import ruamel.yaml as yaml
import logging

class YamlData:

    def __init__(self, file_path: str):
        with open(file_path, 'r', encoding='utf8') as file:
            self.data = yaml.safe_load(file)
        self.logger = logging.getLogger()
        self.file_path = file_path

    def get_nested_value(self, key: str):
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return
        if isinstance(value, dict):
            self.logger.warning(f"Cannot fetch key `{key}` in file `{self.file_path}`")
            return
        return value
    
    def get(self, key: str):
        return self.data.get(key)