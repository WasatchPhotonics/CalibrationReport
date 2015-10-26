""" pyramid views for the application.
"""
import os
import shutil
import logging

from pyramid.response import FileResponse
from pyramid.view import view_config

import colander

from deform import Form
from deform.exception import ValidationFailure

from slugify import slugify

from calibrationreport.pdfgenerator import WasatchSinglePage
from calibrationreport.models import EmptyReport, ReportSchema

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
        filename = "reports/%s/report.png" % serial
        return FileResponse(filename)

    @view_config(route_name="view_pdf")
    def view_pdf(self):
        """ If the matchdict specified serial number directory has a
        calibration report pdf, return it.
        """
        serial = slugify(self.request.matchdict["serial"])
        filename = "reports/%s/report.pdf" % serial
        return FileResponse(filename)

    @view_config(route_name="calibration_report",
                 renderer="templates/calibration_report_form.pt")
    def calibration_report(self):
        """ Process form paramters, create a pdf calibration report form
        and generate a thumbnail view.
        """
        form = Form(ReportSchema(), buttons=("submit",))

        if "submit" in self.request.POST:
            #log.info("submit: %s", self.request.POST)
            controls = self.request.POST.items()
            try:
                appstruct = form.validate(controls)
                rendered_form = form.render(appstruct)

                report = self.populate_data(appstruct)
                self.makedir_write_files(appstruct)
                pdf = WasatchSinglePage(filename=report.filename,
                                        report=report)
                pdf.write_thumbnail()

                return {"form":rendered_form, "appstruct":appstruct}

            except ValidationFailure as exc: 
                #log.exception(exc)
                log.info("Validation failure")
                return {'form':exc.render()} 

        return {"form":form.render()}

    def makedir_write_files(self, appstruct):
        """ With parameters in the post request, create a destination
        directory in reports/ then write each of the post requests files
        to disk.
        """
 
        # Create the directory if it does not exist
        final_dir = "reports/%s" % slugify(appstruct["serial"])
        if not os.path.exists(final_dir):
            log.info("Make directory: %s", final_dir)
            os.makedirs(final_dir)

        if appstruct["top_image_upload"] != colander.null:
            upload = appstruct["top_image_upload"]
            final_file = "%s/top_image.png" % final_dir
            self.single_file_write(upload["fp"], final_file)

        if appstruct["bottom_image_upload"] != colander.null:
            upload = appstruct["bottom_image_upload"]
            final_file = "%s/bottom_image.png" % final_dir
            self.single_file_write(upload["fp"], final_file)

    def single_file_write(self, file_pointer, filename):
        """ Read from the file pointer, write intermediate file, and
        then copy to final destination.
        """
        temp_file = "reports/temp_file"

        file_pointer.seek(0)
        with open(temp_file, "wb") as output_file:
            shutil.copyfileobj(file_pointer, output_file)

        os.rename(temp_file, filename)
        log.info("Saved file: %s", filename) 

    def populate_data(self, appstruct):
        """ Convenience function to fill the data has with the values
        from the POST'ed form.
        """ 
        local = EmptyReport()
        local.serial = appstruct["serial"]
        local.slugged = slugify(appstruct["serial"])
        local.filename = "reports/%s/report.pdf" % local.slugged
        local.coefficient_0 = appstruct["coefficient_0"]
        local.coefficient_1 = appstruct["coefficient_1"]
        local.coefficient_2 = appstruct["coefficient_2"]
        local.coefficient_3 = appstruct["coefficient_3"]

        # Images are optional, set to placeholder if not specified
        if appstruct["top_image_upload"] == colander.null:
            local.top_image_filename = "resources/image0_defined.jpg"
        else:
            local.top_image_filename = "reports/%s/top_image.png" \
                                       % local.slugged

        if appstruct["bottom_image_upload"] == colander.null:
            local.bottom_image_filename = "resources/image1_defined.jpg"
        else:
            local.bottom_image_filename = "reports/%s/bottom_image.png" \
                                          % local.slugged
  

        return local
