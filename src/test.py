import json
import csv
import os
import sys
import logging
import ubidots.device.variables as ubidotsvariables
import data.extremes as dataextremes
import weekly.table as weeklydatatable
import fortnightly.chart as fortnightlychart
import fortnightly.rangeplot as rangeplot
import waternsw.flow as waternswflow
import weekly.bar as weeklybar
import ubidots.device.aws as ubidotsaws
import data.yearly as yearlydata
from dotenv import load_dotenv
import util as utils
import pprint

logging.basicConfig(level=logging.INFO)

def main():
    cwd = os.getcwd()

    load_dotenv()
    #token = os.getenv('ORG_KEY')
    aws_token = os.getenv('CLYDE_AWS_ORG_KEY')
    dw_key = os.getenv('DW_KEY')
    clyde_key = os.getenv('CLYDE_ORG_KEY')
    use_cache = False

    if cwd.split('/')[-1] != 'src':
        logging.error("Please run from src directory")
        sys.exit(1)

    config_path = os.path.join(os.getcwd(), "../config.json")
    # load config as json
    with open(config_path) as f:
        config = json.load(f)

    for site in config['sites']:
        site_config = utils.Config.from_site(site)

        site_directory = os.path.join(os.getcwd(), f'output/{site["directory"]}')
        

        token = ""
        aws_token = ""
        if site['name'].__contains__('Clyde River'):
            token = clyde_key
            aws_token = os.getenv('CLYDE_AWS_ORG_KEY')
        # Create weekly dataset for precipitation bar chart.
        #weeklybar.weekly_precipitation_to_csv(site_directory, aws_token)

        # start_week, end_week = utils.one_week()
        # start_year, end_year = utils.this_year()
        # print(f"Start week: {start_week}, end week: {end_week}")
        # print(f"Start year: {start_year}, end year: {end_year}")

        for variable in site['variables']:
            logging.info(f"Processing {variable} variable.")
            #if use_cache:
            #    variable_list = ubidotsvariables.VariablesList.new_from_cache(site_directory, variable)
            #else:
            #    variable_list = ubidotsvariables.VariablesList.new(variable, site, token)
            #    print(variable_list.__dict__)
            #    pprint.pprint(vars(variable_list))
            #    variable_list.cache(site['directory'], variable)
            
            # Create weekly table csv files
            #weekly_table = weeklydatatable.Table().new(variable_list, token)
            #print(f"weekly_table: {weekly_table.__dict__}")
            #weekly_table.to_csv(variable, f"{site_directory}/weekly-{variable}-table.csv")


        # Create year to date and historical water temperature datasets.
        yearlydata.year_to_date_temperature_to_csv(site_directory, token, site['water_temperature_variables'])



if __name__ == "__main__":
    main()

