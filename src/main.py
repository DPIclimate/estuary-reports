import json
import csv
import os
import sys
import logging
import subprocess
import time
import ubidots.device.variables as ubidotsvariables
import data.extremes as dataextremes
import weekly.table as weeklydatatable
import fortnightly.chart as fortnightlychart
import fortnightly.rangeplot as rangeplot
import waternsw.flow as waternswflow
import weekly.bar as weeklybar
import ubidots.device.aws as ubidotsaws
import data.yearly as yearlydata
import datawrapper.export as datawrapperexport
import datawrapper.download as datawrapperdownload
from dotenv import load_dotenv
import util as utils
import pprint

logging.basicConfig(level=logging.INFO)

overwrite_csvs = True

def main():
    load_dotenv()
    working_directory = os.getenv('WORKING_DIRECTORY')
    dw_key = os.getenv('DW_KEY')
    clyde_river_key = os.getenv('CLYDE_ORG_KEY')
    port_stephens_key = os.getenv('PORT_STEPHENS_ORG_KEY')
    wallis_lakes_key = os.getenv('WALLIS_LAKES_ORG_KEY')
    manning_river_key = os.getenv('MANNING_RIVER_ORG_KEY')
    use_cache = False
    start_dir = os.getcwd()
    cwd = os.getcwd()
    if working_directory is None:
        logging.error("Working directory not set, exiting.")
        logging.error("Please set the WORKING_DIRECTORY environment variable and make sure to include the /src/ folder at the end of it.")
        sys.exit(1)

    if cwd != working_directory:
        logging.info(f"Changing working directory to {working_directory}")
        os.chdir(working_directory)

    config_path = os.path.join(os.getcwd(), "../config.json")
    # load config as json
    with open(config_path) as f:
        config = json.load(f)

    # For all sites in config, create folder for each using directory
    for site in config['sites']:

        site_config = utils.Config.from_site(site)

        token = ""
        if site['name'].__contains__('Clyde River'):
            token = clyde_river_key
        elif site['name'].__contains__('Port Stephens'):
            token = port_stephens_key
        elif site['name'].__contains__('Wallis Lake'):
            token = wallis_lakes_key
        elif site['name'].__contains__('Manning River'):
            token = manning_river_key
        
        
        print(f"Creating and retrieving {site['name']} data.")

        site_directory = os.path.join(os.getcwd(), f'output/{site["directory"]}')
        # Check if data/site['directory'] exists, if not create it.
        if not os.path.exists(site_directory):
            logging.info(f"Directory {site_directory} does not exist, creating it for output.")
            os.makedirs(site_directory)
        else:
            logging.info(f"Directory {site_directory} exists, using it for output.")

        logging.info(f"Creating files for {site['name']} in {site_directory}")
        for file in site['files']:
            file_path = os.path.join(site_directory, f"{file['filepath']}")
            # Check if file exists, if not create it.
            if overwrite_csvs:
                with open(file_path, 'w') as f:
                    f.write("")
            else:
                logging.info(f"File {file['filepath']}.csv exists. Overwrite set to false, skipping file.")
            
            if file['dynamic']:
                #logging.info(f"Creating dynamic columns for {file['name']}.csv")
                with open(file_path, 'w') as f:
                    if file['columns'] == None:
                        writer = csv.writer(f)
                        writer.writerow(utils.weekly_column_names())
                    else:
                        columns = utils.weekly_column_names()
                        for column in file['columns']:
                            columns.append(column)
                        writer = csv.writer(f)
                        writer.writerow(columns)
            else:
                #logging.info(f"Adding static columns for {file['name']}.csv")
                with open(file_path, 'w') as f:
                    writer = csv.writer(f)
                    if file['columns'] is not None:
                        writer.writerow(file['columns'])

        logging.info(f"Created files for {site['name']} in {site_directory}.")
        time.sleep(5)

        # For each sites variables, create csv files.
        for variable in site['variables']:
            #logging.info(f"Processing {variable} variable.")
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

            # Create fortnightly csv files
            fortnightly_range_plot = rangeplot.RangePlot.new(variable_list, token)
            fortnightly_range_plot.to_csv(variable, f"{site_directory}/fortnightly-{variable}.csv")

            # Create weekly table csv files
            weekly_table = weeklydatatable.Table().new(variable_list, token)
            weekly_table.to_csv(variable, f"{site_directory}/weekly-{variable}-table.csv")

            fortnightly_chart = fortnightlychart.Chart().new(variable_list, site, token)
            fortnightly_chart.to_csv(f"{site_directory}/fortnightly-{variable}-chart.csv")

        # For each site, create datasets required using 'site' variable.

        # Create fortnightly dataset for discharge rate WaterNSW.
        fortnight_start, fortnight_end = utils.two_weeks()
        waternswflow.DischargeRate(error_num=None, return_field=None).generate("fortnightly", site_directory, site["water_nsw"])
    
        # Create year dataset for discharge rate WaterNSW.
        year_start, year_end = utils.this_year()
        waternswflow.DischargeRate(error_num=None, return_field=None).generate("yearly", site_directory, site["water_nsw"])

        # Create datasets for last year that were accidentally overwrtitten by the current years data. Only used to run once, do not keep active.
        # waternswflow.DischargeRate(error_num=None, return_field=None).generate("last_year", site_directory, site["water_nsw"])
        
        # Join yearlyndischarge dataset files. (This only joins 1 tributarys data for the current year with previous year/s historical data.)
        if site['name'] == 'Clyde River' or site['name'] == 'Wallis Lakes':
            yearlydata.join_flow_datasets(site_directory, files=site['historical_discharge_files'])

        # Join all tributaries discharge datasets for the current year into 1 data frame.
        waternswflow.join_flow_datasets("yearly", site_directory, site['water_nsw'])

        # Create weekly dataset for precipitation bar chart. Using Variable ID for aggregate data for total daily rainfall values.
        weeklybar.weekly_precipitation_to_csv(site_directory, token, site['ubidots_aws_variable_ids'])

        # Create year to date precipitation datasets.
        yearlydata.year_to_date_precipitation_to_csv(site_directory, token, site['ubidots_aws_variable_ids'])

        # Create combined precipitation dataset for each site. If files for each year exist join them, skip if file doesn't exist.
        yearlydata.join_precipitation_datasets(site_directory)

        # Create year to date and historical water temperature datasets.
        yearlydata.year_to_date_temperature_to_csv(site_directory, token, site['water_temperature_variables'])
        if site['name'] == 'Clyde River':
            yearlydata.historical_temperature_datasets(site_directory)

        datawrapperexport.all_files_to_datawrapper(site_directory, site, dw_key)

        # Download chart images from data wrapper for PDF report generation
        #for file in site['files']:
        #    filename = f"{site_directory}/imgs/{file['name']}.png"
        #    datawrapperdownload.download_image(filename, file['chart_id'], dw_key)

        print(f"{site['name']} complete.")


    for site in config['sites']:
        if site['name'] == 'Clyde Rivers':
            # Generate a PDF report for each site.
            site_directory = os.path.join(os.getcwd(), f'output/{site["directory"]}')
            # Get current working directory
            cwd = os.getcwd()
            # Change working directory to the site_directory/report folder.
            os.chdir(f"{site_directory}/report")
            print("Generating PDF report, executing pdflatex.")
            try:
                cmd = ['pdflatex', '-interaction', 'nonstopmode', '-halt-on-error', 'report.tex']
                proc = subprocess.Popen(cmd)
                proc.communicate()
                retcode = proc.returncode
                if retcode != 0:
                    if os.path.exists(f'{site_directory}/report/report.pdf'):
                        os.unlink(f'{site_directory}/report/report.pdf')
                    raise ValueError(f'pdflatex process failed with return code {retcode}')
                os.unlink(f'{site_directory}/report/report.tex')
                os.unlink(f'{site_directory}/report/report.log')
            except Exception as e:
                print(e)
            os.chdir(cwd)


    # End of process, change back to original working directory if changed.
    if start_dir != working_directory:
        logging.info("Changing back to original user directory.")
        os.chdir(start_dir)


if __name__ == '__main__':
    main()
    
