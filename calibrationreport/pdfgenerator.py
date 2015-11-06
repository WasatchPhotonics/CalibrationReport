""" PDFGenerator - classes for using reportlab to generate wasatch
photonics specific calibration reports.
"""

import os
import time
import logging

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from wand.image import Image as WandImage

from calibrationreport.models import EmptyReport

log = logging.getLogger(__name__)

class WasatchSinglePage(object):
    """ Generate a wasatch photoncis themed calibration report by
    default. All parameters are optional.
    """
    def __init__(self, filename="default.pdf", report=None,
                 return_blob=False):
        self.filename = filename
        self.dir_name = os.path.dirname(__file__)

        # Populate the report object with defaults if not specified
        if report is None:
            report = EmptyReport()

        self.canvas = canvas.Canvas(self.filename, pagesize=letter)
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter

        self.add_serial(report)
        self.add_header_footer_images()
        self.add_product_images(report)
        self.add_coefficients(report)
        if not return_blob:
            log.info("Save: %s", self.filename)
            self.canvas.save()
    
    def return_blob(self):
        """ API compatibility to return generated blob data from qr
        label temporarily writing to disk. If you have a solution with
        tobytes, bytesio and encoder_name, please let me know.
        """
        self.canvas.save()
        temp_file = open(self.filename)
        return temp_file.read()

    def add_serial(self, report):
        """ Add the large serial number text and the calibration
        timestamp.
        """

        serial_text = "<font size=62><i>%s</i></font>" % report.serial
        self.create_paragraph(serial_text, 20, 65)

        time_txt = "Calibrated by: Auto-Calibrated on %s" % time.ctime()
        self.create_paragraph(time_txt, 20, 100)


    def add_header_footer_images(self):
        """ Load the header, footer and side by side imagery .
        """

        # Add the header images
        img_name = "%s/../resources/calibration_report_header.png" \
                   % self.dir_name
        img_head = Image(img_name)
        img_head.drawOn(self.canvas, *self.coord(0, 48, mm))

        img_name = "%s/../resources/calibration_report_footer.png" \
                   % self.dir_name
        img_foot = Image(img_name)
        img_foot.drawOn(self.canvas, *self.coord(0, 280, mm))


    def add_product_images(self, report):
        """ Check if the specified imagery exists, load it into the
        canvas if it is available.
        """
        top_found = os.path.exists(report.top_image_filename)
        bot_found = os.path.exists(report.bottom_image_filename)

        log.info("Add image: %s, %s", report.top_image_filename, report.bottom_image_filename)
        if not top_found or not bot_found:
            log.warn("Not adding unavailable product images")
            return

        # Resize the images with wand first so they will fit in the
        # document as expected. The output size when height scaled to
        # 125px will be close to 300x175 when viewed in the pdf.
        orig_image0_filename = report.top_image_filename
        orig_image1_filename = report.bottom_image_filename

        image0_filename = "temp_image0.png"
        image1_filename = "temp_image1.png"
        with WandImage(filename=orig_image0_filename) as img:
            img.transform(resize="x125")
            img.save(filename=image0_filename)

        with WandImage(filename=orig_image1_filename) as img:
            img.transform(resize="x125")
            img.save(filename=image1_filename)

        # Reload the scaled images, draw with absolute coordinates
        img_zero = Image(image0_filename)
        img_one = Image(image1_filename)

        img_zero.drawOn(self.canvas, *self.coord(135, 100, mm))
        img_one.drawOn(self.canvas, *self.coord(135, 150, mm))
        
    def coord(self, input_x, input_y, unit=1):
        """ Helper class to help position flowables in Canvas objects
        From: http://www.blog.pythonlibrary.org/2012/06/27/\
        reportlab-mixing-fixed-content-and-flowables/
        """
        out_x, out_y = input_x * unit, self.height -  input_y * unit
        return out_x, out_y    
 
    def create_paragraph(self, ptext, input_x, input_y, style=None):
        """ From: http://www.blog.pythonlibrary.org/2012/06/27/\
        reportlab-mixing-fixed-content-and-flowables/
        """
        if not style:
            style = self.styles["Normal"]
        para = Paragraph(ptext, style=style)
        para.wrapOn(self.canvas, self.width, self.height)
        para.drawOn(self.canvas, *self.coord(input_x, input_y, mm))

    def add_coefficients(self, report):
        """ Add the calibration equation image, as well as the
        calibration coefficients defined in the report object.
        """
        img_name = "%s/../resources/calibration_text_and_equation.png" \
                   % self.dir_name
        img_equ = Image(img_name)
        img_equ.drawOn(self.canvas, *self.coord(40, 180, mm)) 

        pfx_txt = "Where 'p' is pixel index, and:"
        self.create_paragraph(pfx_txt, 60, 190)

        c0_txt = "Coefficient <b>C0 =</b> %s" % report.coefficient_0
        self.create_paragraph(c0_txt, 60, 200)
        c1_txt = "Coefficient <b>C1 =</b> %s" % report.coefficient_1
        self.create_paragraph(c1_txt, 60, 208)
        c2_txt = "Coefficient <b>C2 =</b> %s" % report.coefficient_2
        self.create_paragraph(c2_txt, 60, 216) 
        c3_txt = "Coefficient <b>C3 =</b> %s" % report.coefficient_3
        self.create_paragraph(c3_txt, 60, 224)


    def write_thumbnail(self):
        """ Reload the file written to disk in init, generate a png of
        the top page, write it to disk and return the filename.
        """
        png_filename = self.filename.replace(".pdf", ".png")
        first_page_file = "%s[0]" % self.filename
        with WandImage(filename=first_page_file) as img:
            img.resize(496, 701) # A4 ratio 2480x2408
            img.save(filename=png_filename)

        log.info("Generated top thumbnail for %s", self.filename)
        return png_filename
