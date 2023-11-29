import json

class JSONPathExtractor:
    """
    Utilizzo della classe
    from libs.json_path_extractor import JSONPathExtractor

    extractor = JSONPathExtractor('your_json_file.json')  # Sostituisci con il nome del tuo file JSON
    microeconomics_indicator_path = extractor.get_path_value('file_path.microeconomics_indicator')
    print(f"Percorso per 'microeconomics_indicator': {microeconomics_indicator_path}")
    """
    def __init__(self):
        self.json_file_name = f"json_files/config_files.json"
        self.data = self._load_json()

    def _load_json(self):
        with open(self.json_file_name, 'r') as file:
            return json.load(file)

    def get_path_value(self, path):
        current_data = self.data
        for key in path.split('.'):
            current_data = current_data.get(key)
            if current_data is None:
                return None
        return current_data
    