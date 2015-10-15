""" pyramid views for the application.
"""
import os
import shutil
import logging

from pyramid.response import FileResponse
from pyramid.view import view_config

from slugify import slugify

from calibrationreport.pdfgenerator import WasatchSinglePage
from calibrationreport.models import EmptyReport

log = logging.getLogger(__name__)

class CalibrationReportViews(object):
    """ Generate pdf and png content of calibration reports based on
    fields supplied by the user.
    """
    def __init__(self, request):
        self.request = request

    @view_config(route_name="view_thumbnail")
    def view_thumbnail(self):
        """ If the matchdict specified serial number directory has a
        first page calibration report png thumbnail, return it.
        """
        serial = slugify(self.request.matchdict["serial"])
        filename = "database/%s/report.png" % serial
        if not os.path.exists(filename):
            log.warn("Can't find thumbnail: %s", filename)
            filename = "database/placeholders/thumbnail_start.png"

        return FileResponse(filename)

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
            pdf_save = "database/%s/report.pdf" % slugify(report.serial)
            pdf = WasatchSinglePage(filename=pdf_save, report=report)
            pdf.write_thumbnail()

        pdf_link = "%s/report.pdf" % slugify(report.serial)
        links = {"pdf_link":pdf_link}
        images = {"thumbnail":"%s/report.png" % slugify(report.serial)}

        return dict(fields=report, links=links, images=images)

    def populate_report(self):
        """ Using the post fields, make the report object match the
        supplied user configuration. If uploading of files is succesful,
        assign the temporary filenames to the report object.
        """
        report = EmptyReport()
        report.serial = self.request.POST["serial"]
        report.coeff_0 = self.request.POST["coeff_0"]
        report.coeff_1 = self.request.POST["coeff_1"]
        report.coeff_2 = self.request.POST["coeff_2"]
        report.coeff_3 = self.request.POST["coeff_3"]

        # If the image0 value is not populated, set it to the
        # placeholder image
        img0_content = self.request.POST["image0_file_content"]
        if img0_content == "":
            img0_content = WrapStorage("image0_placeholder.jpg")

        self.write_file(report.serial, "image0.png", img0_content.file)
        report.image0 = "database/%s/image0.png" \
                        % slugify(report.serial)

        img1_content = self.request.POST["image1_file_content"]
        if img1_content == "":
            img1_content = WrapStorage("image1_placeholder.jpg")

        self.write_file(report.serial, "image1.png", img1_content.file)
        report.image1 = "database/%s/image1.png" \
                        % slugify(report.serial)

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
        final_dir = "database/%s" % slugify(serial)
        if not os.path.exists(final_dir):
            log.info("Make directory: %s", final_dir)
            os.makedirs(final_dir)

        final_file = "%s/%s" % (final_dir, destination)

        os.rename(temp_file, final_file)
        log.info("Saved file: %s", final_file)

class WrapStorage(object):
    """ Create a storage object that references a file for use in
    place of invalid uploaded objects from POST.
    """
    def __init__(self, source_file_name):
        prefix = "database/placeholders"
        self.filename = "%s/%s" % (prefix, source_file_name)
        self.file = file(self.filename)
        log.info("Wrap storage file: %s", self.filename)
