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
    config.add_route("top_thumbnail", "/top_thumbnail/{serial}")
    config.add_route("mosaic_thumbnail", "/mosaic_thumbnail/{serial}")
    config.add_route("add_pdf", "/add_pdf")
    config.scan()
    return config.make_wsgi_app()
