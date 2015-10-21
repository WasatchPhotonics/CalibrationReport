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
        log.info("Show thumbnail %s", serial)
        filename = "reports/%s/report.png" % serial
        if not os.path.exists(filename):
            log.warn("Can't find thumbnail: %s", filename)
            filename = "resources/thumbnail_start.png"

        return FileResponse(filename)

    @view_config(route_name="blank_thumbnail")
    def blank_thumbnail(self):
        """ Match a route without the serial in matchdict, return the
        placeholder image.
        """
        log.info("Return blank thumbnail")
        return FileResponse("resources/S_00101_report.png")
    

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
        schema = ReportSchema()
        form = Form(schema, buttons=("submit",))
        local = EmptyReport()

        if "submit" in self.request.POST:
            #log.info("submit: %s", self.request.POST)
            try:
                # Deserialize into hash on validation - capture is the
                # "appstruct" in deform nomenclature
                controls = self.request.POST.items()
                captured = form.validate(controls)

                self.populate_data(local, captured)
                self.write_files(local)
                pdf_save = "reports/%s/report.pdf" \
                           % slugify(local.serial)
                pdf = WasatchSinglePage(filename=pdf_save, report=local)
                pdf.write_thumbnail()

                # Re-render the form with the fields already populated 
                return dict(data=local, form=form.render(captured))
                
            except ValidationFailure as exc:
                #log.exception(exc)
                log.critical("Validation failure, return default form")
                return dict(data=local, form=exc.render())

        return dict(data=local, form=form.render())


    def write_files(self, upload_obj):
        """ With file(s) from the post request, write to a temporary 
        file, then ultimately to the destination specified.
        """
        # Create the directory if it does not exist
        final_dir = "reports/%s" % slugify(upload_obj.serial)
        if not os.path.exists(final_dir):
            log.info("Make directory: %s", final_dir)
            os.makedirs(final_dir)

       
    def populate_data(self, local, captured):
        """ Convenience function to fill the data has with the values
        from the POST'ed form.
        """ 
        local.serial = captured["serial"]
        local.coefficient_0 = captured["coefficient_0"]
        local.coefficient_1 = captured["coefficient_1"]
        local.coefficient_2 = captured["coefficient_2"]
        local.coefficient_3 = captured["coefficient_3"]
  
        # Images are optional, set to placeholder if not specified
        if captured["top_image_upload"] == colander.null:
            local.top_image_filename = "resources/image0_defined.jpg"
        else:
            top_filename = captured["top_image_upload"]["filename"]
            local.top_image_filename = top_filename

        if captured["bottom_image_upload"] == colander.null:
            local.bottom_image_filename = "resources/image1_defined.jpg"
        else:
            bottom_filename = captured["bottom_image_upload"]["filename"]
            local.bottom_image_filename = bottom_filename

        return local

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
        report.image0 = "reports/%s/image0.png" \
                        % slugify(report.serial)

        img1_content = self.request.POST["image1_file_content"]
        if img1_content == "":
            img1_content = WrapStorage("image1_placeholder.jpg")

        self.write_file(report.serial, "image1.png", img1_content.file)
        report.image1 = "reports/%s/image1.png" \
                        % slugify(report.serial)

        return report

    def write_file(self, serial, destination, upload_file):
        """ With file from the post request, write to a temporary file,
        then ultimately to the destination specified.
        """
        temp_file = "reports/temp_file"
        upload_file.seek(0)
        with open(temp_file, "wb") as output_file:
            shutil.copyfileobj(upload_file, output_file)

        # Create the directory if it does not exist
        final_dir = "reports/%s" % slugify(serial)
        if not os.path.exists(final_dir):
            log.info("Make directory: %s", final_dir)
            os.makedirs(final_dir)

        final_file = "%s/%s" % (final_dir, destination)

        os.rename(temp_file, final_file)
        log.info("Saved file: %s", final_file)
