""" Defines application main, routes and configuration options for the
pyramid application.
"""
from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application. Check the
    config/.ini files for more information.
    """
    config = Configurator(settings=settings)
    config.include("pyramid_chameleon")
    config.add_static_view("static", "static", cache_max_age=3600)
    config.add_route("cal_report", "/")
    config.add_route("view_pdf", "/view_pdf/{serial}")
    config.add_route("view_thumbnail", "/view_thumbnail/{serial}")
    config.scan()
    return config.make_wsgi_app()
