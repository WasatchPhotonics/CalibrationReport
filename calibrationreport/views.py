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
    
    @view_config(route_name="cal_report", renderer="templates/home.pt")
    def cal_report(self):
        """ Update the currently displayed calibration report with the
        fields submitted from post.
        """
        report = EmptyReport()
        if "form.submitted" in self.request.params:
            report = self.populate_report()

        self.write_report(report)

        pdf_link = "%s/report.pdf" % report.serial
        links = {"pdf_link":pdf_link}

        return dict(fields=report, links=links)

    def write_report(self, report):
        """ Populate a pdf document and write to disk base on the fields
        in the report object.
        """

        report_path = "database/%s" % report.serial
        if not os.path.exists(report_path):
            os.makedirs(report_path)
        else:
            log.warn("Ovewriting path info %s", report_path)

        filename = "database/%s/report.pdf" % report.serial
                 
        pdf = WasatchSinglePage(filename)

    def populate_report(self):
        """ Using the post fields, make the report object match the
        supplied user configuration.
        """
        report = EmptyReport()
        report.serial = self.request.POST["serial"]
        report.coeff_0 = self.request.POST["coeff_0"]
        report.coeff_1 = self.request.POST["coeff_1"]
        report.coeff_2 = self.request.POST["coeff_2"]
        report.coeff_3 = self.request.POST["coeff_3"]


        img0_content = self.request.POST["image0_file_content"]
        report.image0 = img0_content.filename

        img1_content = self.request.POST["image1_file_content"]
        report.image1 = img1_content.filename
        return report

