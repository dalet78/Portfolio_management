# from macro_economic.import_me_data import WorldBankDataDownloader as wbd
from portfolio_management.macro_economic.import_fred_data import FredDataDownloader
from portfolio_management.libs.json_dict_extractor import JsonToDictConverter
from portfolio_management.macro_economic.create_me_report import CreateReport

def test_json_extract ():
        indicators_dict = JsonToDictConverter(config_path='file_path.microeconomics_indicator')
        config_dict= indicators_dict.convert_to_dict()
        test = FredDataDownloader(api_key=config_dict["api_key"], config_dict= config_dict)
        test.save_data_to_csv(country="USA")
        report = CreateReport(config_dict= config_dict, country="USA")
        report.report_create()
        

if __name__ == "__main__":
    test_json_extract()