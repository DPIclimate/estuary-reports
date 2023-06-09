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
from dotenv import load_dotenv
import util as util
import pprint

logging.basicConfig(level=logging.INFO)

overwrite_csvs = True

def main():
    load_dotenv()
    #token = os.getenv('ORG_KEY')
    aws_token = os.getenv('AWS_ORG_KEY')
    dw_key = os.getenv('DW_KEY')
    clyde_key = os.getenv('CLYDE_ORG_KEY')
    use_cache = False

    cwd = os.getcwd()
    if cwd.split('/')[-1] != 'src':
        logging.error("Please run from src directory")
        sys.exit(1)

    config_path = os.path.join(os.getcwd(), "../config.json")
    # load config as json
    with open(config_path) as f:
        config = json.load(f)

    # For all sites in config, create folder for each using directory
    for site in config['sites']:
        site_config = util.Config.from_site(site)

        print(site_config)

        token = ""
        if site['name'].__contains__('Clyde River'):
            token = clyde_key
        elif site['name'] == 'Wallace Lakes':
            token = clyde_key
        else:
            token = clyde_key
        
        print(f"{site['name']}: {token}")

        site_directory = os.path.join(os.getcwd(), f'output/{site["directory"]}')
        # Check if data/site['directory'] exists, if not create it.
        if not os.path.exists(site_directory):
            logging.info(f"Directory {site_directory} does not exist, creating it.")
            os.makedirs(site_directory)
        else:
            logging.info(f"Directory {site_directory} exists, switching to it.")

        logging.info(f"Creating files for {site['name']} in {site_directory}")
        for file in site['files']:
            file_path = os.path.join(site_directory, f"{file['name']}.csv")
            # Check if file exists, if not create it.
            if overwrite_csvs:
                with open(file_path, 'w') as f:
                    f.write("")
            else:
                logging.info(f"File {file['name']}.csv exists. Overwrite set to false, skipping file.")
            
            if file['dynamic']:
                #logging.info(f"Creating dynamic columns for {file['name']}.csv")
                with open(file_path, 'w') as f:
                    if file['columns'] == None:
                        writer = csv.writer(f)
                        writer.writerow(util.weekly_column_names())
                    else:
                        columns = util.weekly_column_names()
                        for column in file['columns']:
                            columns.append(column)
                        writer = csv.writer(f)
                        writer.writerow(columns)
            else:
                #logging.info(f"Adding static columns for {file['name']}.csv")
                with open(file_path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(file['columns'])
        
        for variable in site['variables']:
            logging.info(f"Processing {variable} variable.")
            if use_cache:
                variable_list = ubidotsvariables.VariablesList.new_from_cache(site_directory, variable)
            else:
                variable_list = ubidotsvariables.VariablesList.new(variable, site, token)
                print(variable_list.__dict__)
                pprint.pprint(vars(variable_list))
                variable_list.cache(site['directory'], variable)

            # Create weekly max and min dataset
            extremes = dataextremes.Extremes()
            extremes.new(variable_list, site, token)
            extremes.to_csv(f"{site_directory}/weekly-{variable}-extremes.csv")

            print(f"Variables: {variable_list.__dict__}")

            # Create fortnightly csv files
            fortnightly_range_plot = rangeplot.RangePlot.new(variable_list, token)
            fortnightly_range_plot.to_csv(variable, f"{site_directory}/fortnightly-{variable}.csv")

            # Create weekly table csv files
            weekly_table = weeklydatatable.Table().new(variable_list, token)
            print(f"weekly_table: {weekly_table.__dict__}")
            weekly_table.to_csv(variable, f"{site_directory}/weekly-{variable}-table.csv")

            fortnightly_chart = fortnightlychart.Chart().new(variable_list, site, token)
            #fortnightly_chart.to_csv(variable)

    print("Complete.")


if __name__ == '__main__':
    main()
    