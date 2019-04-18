from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button
from .QueryCatalog import *

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    # dict = {'brand': "111", 'model': "222"}     # For testing
    dict = GetAllRegions()

    context = {
        'dict': dict
    }

    return render(request, 'servicecatalogurls/home.html', context)


def about(request):
    """
    Controller for the About page.
    """

    context = {}
    return render(request, 'servicecatalogurls/about.html', context)


def queryresult(request):
    """
    Controller for the QueryResult page.
    """
    regionID = request.GET['region_Picklist']

    # For debug/testing...
    # time.sleep(2)
    # errList, badCatalogList = QueryServiceCatalog_DummyTestReturn(regionID)    # For testing
    errList, badCatalogList = QueryServiceCatalog(regionID)

    context = {
        "errList": errList,
        "badCatalogList": badCatalogList
    }

    # return render(request, 'servicecatalogurls/queryresult.html', {"errList": errList, "badCatalogList": badCatalogList})
    return render(request, 'servicecatalogurls/queryresult.html', context)



    context = {}
    return render(request, 'servicecatalogurls/about.html', context)



