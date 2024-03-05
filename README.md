# estuary-reports

#### A dynamic NSW Estuary data report compiler and generator. 
#### Created by [Harvey Bates](https://github.com/HarveyBates) under [pilot-reports](https://github.com/DPIclimate/pilot-reports) repo, expanded and currently maintained by [Ben Sefton](https://github.com/bsefton12) as [Estuary-Reports](https://dpiclimate.github.io/estuary-reports/).
#### Built using Python, LaTeX and DataWrapper using timeseries data from WaterNSW and Ubidots IoT data platform.

## Data Wrapper Charts
#### Charts are initialised using the app.datawrapper.de web app, where data is then pushed to chart end-points to update and publish. After a chart is published it is downloaded locally as a png to be used in PDF report generation.

## Ubidots IoT Data Platform
#### The Ubidots data platform is used to host all timeseries data with API features such as data aggregation across multiple devices variables it is ideal for grouped device data reporting.

## Custom Docker Image
#### Requires building on an x86 machine, will not run on GitHub Actions Runners if built on ARM.

## LaTeX PDF Report
#### Creates a PDF report using Latexmk within the texlive distribution.
