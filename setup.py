import os

from setuptools import setup, find_packages

# These will break the travis build. 
#here = os.path.abspath(os.path.dirname(__file__))
#with open(os.path.join(here, "README.txt")) as f:
#    README = f.read()
#with open(os.path.join(here, "CHANGES.txt")) as f:
#    CHANGES = f.read()

README=""
CHANGES=""

requires = [
    "pyramid",
    "pyramid_chameleon",
    "pyramid_debugtoolbar",
    "pyramid_tm",
    "waitress",
    "WebTest",
    "requests",
    "python-slugify",
    "wand",
    "reportlab",
    ]

setup(name="calibrationreport",
      version="0.0",
      description="calibrationreport",
      long_description=README + "\n\n" + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author="",
      author_email="",
      url="",
      keywords="web wsgi bfg pylons pyramid",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite="calibrationreport",
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = calibrationreport:main
      """,
      )
