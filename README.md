<a href="https://www.servirglobal.net//">
    <img src="https://www.servirglobal.net/Portals/0/Images/Servir-logo.png" alt="SERVIR Global"
         title="SERVIR Global" align="right" />
</a>


SERVIR Service Catalogue - Invalid URL Checker
==============================================
> Tethys application (Django/Python) for verifying user-entered URLs in the SERVIR Global Service Catalogue are valid/reachable via the internet. Uses the Service Catalogue API to retrieve data about each Service (specifically the "Data", "Tools", "News", and "Training Materials" URL links) and verifies that the specified data is valid.  This is meant to be an admin tool for SERVIR Global admins.

## Introduction:
The [SERVIR Global Service Catalogue](https://www.servirglobal.net/ServiceCatalogue/) is a collection of services from the SERVIR program and is a culmination of all services that are provided by the SERVIR regional hubs.  Each of the regional hubs post service entries into the catalogue along with Data Output, News, Tools, Training Materials, and other data related to each one of the services.  From time to time, the links to these related data, news, tools, and training materials changes or gets out of date and we needed a good way to identify the invalid URLs when that happens.  This tool uses the Service Catalogue API to retrieve all of the services from the catalogue and processes the Data, News, Tools, and Training Materials for each service to verify that the corresponding URLs are valid.

Another check was added to verify that all "Data Output" URLs link to the [SERVIR Global Data Catalogue](http://gis1.servirglobal.net:8080/geonetwork/). All output datasets resulting from SERVIR services should be documented and have entries in the Global Data Catalogue.  As the Global Data Catalogue harvests metadata entries from all of the SERVIR hubs, we want to ensure that the datasets are available via the Global Catalogue, which ensures that the data is created in the regional hub catalogues.

The goal is to identify problematic URLs and to provide enough detail so that an admin can quickly navigate to the related service within the catalogue, and find the section and specific entry that needs to be corrected.

## Details:
The components of this app are:
1. A simple web front-end UI built using the Tethys framework.  The UI consists of:
 - a main page containing a list of the SERVIR regions to choose from (or All), and a button to initiate the API search of the Service Catalogue for all services related to the chosen region.
 - an about page that provides more details about the tool.
 - a results page that displays 2 tables. One table is for entries who's URL link returns an error code when trying to access the site.  The second table is for "Data" specific entries that do not link to the Global Data Catalogue.
2. A python module back-end that retrieves the specified service records using the exposed API and processes through the related fields and checks that certain URLs can be accessed. Any that are found to return an error status code when accessed (or that do not link to the desired source website) are collected and returned to the calling function. The python functions are well documented in the code, so please see the code for more details.

Please see "Servir - ServiceCatalogue GraphQL API.PDF" for more details on the API used to access info from the Service Catalog.

## Environment:
This tool was developed using:
 - Tethys v 2.1.0
 - Django v. 1.11.20  (includes Python 3.6.7, Django-Bootstrap3 11.0, CSS, javascript, and jQuery)

The project follows the standard Django application template and is called ServiceCatalogURLs. The majority of the python code logic is in QueryCatalog.py.  Below is the source hierarchy:
```
`<app_source folder>/
`                    ReadMe.md (this file)
`                    Servir - ServiceCalatogue GraphQL API.PDF
`                    setup.py
`                    tethysapp/
`                              servicecatalogurls/
`                                                 api.py
`                                                 app.py
`                                                 controllers.py
`                                                 handoff.py
`                                                 model.py
`                                                 QueryCatalog.py
`                                                 public/
`                                                        css/
`                                                            main.css
`                                                        images/
`                                                               icon.gif
`                                                        js/
`                                                           main.js
`                                                 templates/
`                                                           servicecatalogurls/
`                                                                              about.html
`                                                                              base.html
`                                                                              home.html
`                                                                              queryresult.html
`                                                 tests/
`                                                       tests.py
`                                                 workspaces/
`                                                            app-workspaces/
`                                                            user_workspaces/
`
```

## Instructions to deploy:
1.  Install and configure [Tethys](http://docs.tethysplatform.org/en/stable/index.html) per [installation instructions](http://docs.tethysplatform.org/en/stable/installation.html#).
2.  Clone this repository to your desired app location on your Tethys server and configure the app to run in the Tethys environment.
3.  Start your browser and navigate to the Tethys Apps home page.
Tethys App tutorials are at: [http://docs.tethysplatform.org/en/stable/tutorials.html](http://docs.tethysplatform.org/en/stable/tutorials.html)
