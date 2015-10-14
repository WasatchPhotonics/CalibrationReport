""" pyramid views for the application.
"""
import os
import sys
import shutil
import logging

from subprocess import Popen

from pyramid.response import Response, FileResponse
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from slugify import slugify

from wand.image import Image

from calibrationreport.pdfgenerator import WasatchSinglePage
from calibrationreport.models import EmptyReport

log = logging.getLogger(__name__)


class CalibrationReportViews:
    """ Generate pdf and png content of calibration reports based on
    fields supplied by the user.
    """
    def __init__(self, request):
        self.request = request
    
    @view_config(route_name="view_pdf")
    def view_pdf(self):
        """ If the matchdict specified serial number directory has a
        calibration report pdf, return it.
        """
        serial = slugify(self.request.matchdict["serial"])
        filename = "database/%s/report.pdf" % serial
        return FileResponse(filename)
 
    @view_config(route_name="cal_report", renderer="templates/home.pt")
    def cal_report(self):
        """ Update the currently displayed calibration report with the
        fields submitted from post.
        """
        report = EmptyReport()

        if "form.submitted" in self.request.params:
            report = self.populate_report()
            pdf_save = "database/%s/report.pdf" % report.serial
            pdf = WasatchSinglePage(filename=pdf_save, report=report)

        pdf_link = "%s/report.pdf" % report.serial
        links = {"pdf_link":pdf_link}

        return dict(fields=report, links=links)


    def populate_report(self):
        """ Using the post fields, make the report object match the
        supplied user configuration. If uploading of files is succesful,
        assign the temporary filenames to the report object.
        """
        report = EmptyReport()
        report.serial = slugify(self.request.POST["serial"])
        report.coeff_0 = self.request.POST["coeff_0"]
        report.coeff_1 = self.request.POST["coeff_1"]
        report.coeff_2 = self.request.POST["coeff_2"]
        report.coeff_3 = self.request.POST["coeff_3"]

        img0_content = self.request.POST["image0_file_content"]
        self.write_file(report.serial, "image0.png", img0_content.file)
        report.image0 = "database/%s/image0.png" % report.serial

        img1_content = self.request.POST["image1_file_content"]
        self.write_file(report.serial, "image1.png", img1_content.file)
        report.image1 = "database/%s/image1.png" % report.serial

        return report


    def write_file(self, serial, destination, upload_file):
        """ With file from the post request, write to a temporary file,
        then ultimately to the destination specified.
        """
        temp_file = "database/temp_file"
        upload_file.seek(0)
        with open(temp_file, "wb") as output_file:
            shutil.copyfileobj(upload_file, output_file)

        # Create the directory if it does not exist
        final_dir = "database/%s" % serial
        if not os.path.exists(final_dir):
            log.info("Make directory: %s", final_dir)
            os.makedirs(final_dir)

        final_file = "%s/%s" % (final_dir, destination)

        os.rename(temp_file, final_file)
        log.info("Saved file: %s" % final_file)
