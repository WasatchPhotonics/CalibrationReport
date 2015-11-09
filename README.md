# CalibrationReport
[![Build Status](https://travis-ci.org/WasatchPhotonics/CalibrationReport.svg?branch=master)](http://travis-ci.org/WasatchPhotonics/CalibrationReport) [![Coverage Status](https://coveralls.io/repos/WasatchPhotonics/CalibrationReport/badge.svg?branch=master&service=github)](https://coveralls.io/github/WasatchPhotonics/CalibrationReport?branch=master)

Web service to create calibration reports for wasatch photonics
spectrometers. Use a responsive web form to accept a serial number,
calibration coefficients and (optional) product imagery. Create a PDF
document and graphical thumbnail, store forever.


![CalibrationReport screenshot](/resources/demo.gif "Calibration Report screenshot")

Getting Started
---------------
    Create a python virtual environment
    sudo dnf install freetype-devel
    sudo dnf install gcc
    sudo dnf install libjpeg-devel
    sudo dnf install zlib-devel
    sudo dnf install ImageMagick-devel

- cd _directory containing this file_

- $VENV/bin/python setup.py develop

- $VENV/bin/nosetests --cover-erase --with-coverage --cover-package=stickercode

- $VENV/bin/pserve config/development.ini

