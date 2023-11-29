from libs.json_path_extractor import JSONPathExtractor


class JsonToDictConverter():
    """
    Una classe per convertire un file JSON in un dizionario Python.
    # Esempio d'uso:
    # converter = JsonToDictConverter('path_to_json_file.json', 'countries.USA.indicators')
    # dictionary = converter.convert_to_dict()
    # print(dictionary)
    """

    def __init__(self,config_path, path=None):
        """
        Inizializza la classe con il percorso del file JSON e un percorso opzionale 
        a una specifica sezione del file JSON.
        :param json_file_path: Percorso al file JSON.
        :param path: Percorso opzionale a una specifica sezione del file JSON in notazione a punti.

        """
        self.extractor = JSONPathExtractor()
        self.json_file_path = self.extractor.get_path_value(path=config_path)
        self.path = path

    def convert_to_dict(self):
        """
        Legge il file JSON e lo converte in un dizionario. Se viene fornito un percorso, 
        restituisce la sezione specifica del file JSON.

        :return: Una rappresentazione dizionario del file JSON o di una sua specifica sezione.
        """
        try:
            with open(self.json_file_path, 'r') as file:
                import json
                data = json.load(file)

            if self.path:
                for part in self.path.split('.'):
                    data = data.get(part, {})
                    if not data:
                        break

            return data
        except Exception as e:
            return {"error": str(e)}

