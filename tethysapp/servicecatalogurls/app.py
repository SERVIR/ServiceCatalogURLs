from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting


class Servicecatalogurls(TethysAppBase):
    """
    Tethys app class for ServiceCatalogURLs.
    """

    name = 'ServiceCatalogURLs'
    index = 'servicecatalogurls:home'
    icon = 'servicecatalogurls/images/URLs.GIF'
    package = 'servicecatalogurls'
    root_url = 'servicecatalogurls'
    color = '#458b74'
    description = 'Checks the SERVIR Service Catalog for invalid URLs.'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='servicecatalogurls',
                controller='servicecatalogurls.controllers.home'
            ),
            UrlMap(
                name='about',
                url='servicecatalogurls/about',
                controller='servicecatalogurls.controllers.about'
            ),
            UrlMap(
                name='queryresult',
                url='servicecatalogurls/queryresult',
                controller='servicecatalogurls.controllers.queryresult'
            ),
        )

        return url_maps


    def custom_settings(self):
        """
        Example custom_settings method.
        """
        custom_settings = (
            CustomSetting(
                name='Region',
                type=CustomSetting.TYPE_STRING,
                description='Region to process.',
                required=False
            ),
        )
        return custom_settings
