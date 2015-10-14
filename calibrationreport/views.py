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

log = logging.getLogger(__name__)

class CalibrationReportViews:
    """ Generate pdf and png content of calibration reports based on
    fields supplied by the user.
    """
    def __init__(self, request):
        self.request = request
    
    @view_config(route_name="cal_report", renderer="templates/home.pt")
    def cal_report(self):
        fields = self.generate_empty_cal_report()
        return dict(fields=fields)

    def generate_empty_cal_report(self):
        """ placeholder object returned for use as the empty calibration
        report fields.
        """
        class EmptyReport(object):
            serial = "unspecified"
            coeff_0 = "unspecified"

        empty = EmptyReport()
        return empty

class ThumbnailViews:
    """ Return png objects from disk where the serial number is found,
    otherwise return placeholder imagery.
    """
    def __init__(self, request):
        self.request = request

        self.sanitize_parameters()
        #log.info("About to try serial assignment")
        self.serial = self.request.matchdict["serial"]
        self.prefix = "database/imagery"
        #log.info("Setup with serial %s", self.serial)

    def sanitize_parameters(self):
        """ slugify the parameters to prevent relative path names in the
        system.
        """
        #log.info("Sanitize parameters")
        serial = "unspecified"
        try:
            serial = self.request.matchdict["serial"]
        except KeyError:
            log.warn("No serial key specified")

        self.request.matchdict["serial"] = slugify(serial)

    @view_config(route_name="add_pdf",
                 renderer="templates/add_pdf.pt")
    def add_pdf(self):
        """ Display the pdf addition form, accept an uploaded file and
        generation thumbnail representations.
        """
        if "form.submitted" in self.request.params:
            if "serial" not in self.request.params:
                log.critical("Must submit a serial")
                return HTTPNotFound()

            serial = self.request.POST["serial"] 
            if serial == "":
                log.critical("Must populate serial")
                return HTTPNotFound()

            serial = slugify(serial)
            file_content = self.request.POST["file_content"]
            filename = file_content.filename
            self.write_file(serial, "original.pdf", file_content.file)
            self.generate_pdf_thumbnail(serial)
            log.info("Callg enerate mosaic")
            self.generate_mosaic_thumbnail(serial)
        
            return dict(serial=serial, filename=filename)
             
            
        return dict(serial="", filename="")

    def generate_mosaic_thumbnail(self, serial):
        """ Convert the uploaded pdf to a wide image of overlaid, titled
        pages for display as a sort of line of polaroids.
        """
        pdf_filename = "%s/%s/original.pdf" % (self.prefix, serial)
        tile_dir = "%s/%s/tiles/" % (self.prefix, serial)

        # delete any previously generated tiles
        try:
            log.info("Delete old %s", tile_dir)
            shutil.rmtree(tile_dir)
        except OSError, e:
            log.exception(e)

        log.info("Make tile directory: %s", tile_dir)
        os.makedirs(tile_dir)
      
        # The with Image concept with wand api and multi page documents
        # does not seem to handle resizing correctly. Only the last file
        # is saved with the new filesize. Use command line version
        # instead

        log.info("Resize pdf pages")
        wtpage_file = "%s/wt_page.png" % tile_dir
        cmd_options = ["convert", pdf_filename, wtpage_file]
       
            
        self.pipe = Popen(cmd_options)
        self.pipe.communicate()

       
        # Is there a python api that supports montage from imagemagick?
        # As of 2015-10-13 14:29 the only way appears to be calling the
        # command line version, fortunately installed by default on all
        # travis system images. 
        log.info("Combine into polaroid row")
        wt_files = "%s/wt_*.png" % tile_dir
        out_file = "%s/%s/mosaic_thumbnail.png" % (self.prefix, serial)
        cmd_options = ["montage",  wt_files,  
                       "+polaroid",
                       "-tile", "9x1",  
                       "-geometry", "-10+2", 
                       "-resize", "10%", out_file]

        self.pipe = Popen(cmd_options)
        self.pipe.communicate()
        

    def generate_pdf_thumbnail(self, serial):
        """  Convert the first page of the designated pdf to png format
        using imagemagick.
        """
        pdf_filename = "%s/%s/original.pdf[0]" % (self.prefix, serial)
        temp_file = "%s/%s/top_thumbnail.png" % (self.prefix, serial)

        with Image(filename=pdf_filename) as img:
            img.resize(306, 396)
            img.save(filename=temp_file)

        log.info("Saved top thumbnail")

    def write_file(self, serial, destination, upload_file):
        """ With file from the post request, write to a temporary file,
        then ultimately to the destination specified.
        """
        temp_file = "database/temp_file"
        upload_file.seek(0)
        with open(temp_file, "wb") as output_file:
            shutil.copyfileobj(upload_file, output_file)

        # Create the directory if it does not exist
        final_dir = "%s/%s" % (self.prefix, serial)
        if not os.path.exists(final_dir):
            log.info("Make directory: %s", final_dir)
            os.makedirs(final_dir)

        final_file = "%s/%s" % (final_dir, destination)

        os.rename(temp_file, final_file)
        log.info("Saved file: %s" % final_file)

    @view_config(route_name="top_thumbnail")
    def top_thumbnail(self):
        """ Display the top page thumbnail of the specified pdf if it
        exists.
        """
        file_name = "%s/%s/top_thumbnail.png" \
                    % (self.prefix, self.serial)
        location = "%s/top_placeholder.png" % self.prefix

        if os.path.exists(file_name):
            location = file_name

        return FileResponse(location)

    @view_config(route_name="mosaic_thumbnail")
    def mosaic_thumbnail(self):
        """ Display the mosaic multi page thumbnail of the pdf if it
        exists.
        """
        file_name = "%s/%s/mosaic_thumbnail.png" \
                    % (self.prefix, self.serial)
        location = "%s/mosaic_placeholder.png" % self.prefix

        if os.path.exists(file_name):
            location = file_name

        return FileResponse(location)
