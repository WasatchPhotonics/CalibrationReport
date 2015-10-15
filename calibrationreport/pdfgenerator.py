""" PDFGenerator - classes for using reportlab to generate wasatch
photonics specific calibration reports.
"""

import time
import logging

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from wand.image import Image as WandImage

from calibrationreport.models import EmptyReport

log = logging.getLogger(__name__)

class WasatchSinglePage(object):
    """ Generate a wasatch photoncis themed calibration report by
    default. All parameters are optional.
    """
    def __init__(self, filename="default.pdf", report=None):
        self.filename = filename

        # Populate the report object with defaults if not specified
        if report is None:
            report = EmptyReport()

        self.doc = SimpleDocTemplate(self.filename, pagesize=letter,
                                     rightMargin=72, leftMargin=72,
                                     topMargin=72, bottomMargin=18)

        story = []
        self.add_header(story, report)
        self.add_images(story, report)
        self.add_coefficients(story, report)
        self.doc.build(story)

    def add_coefficients(self, story, report):
        """ Add the calibration equation image, as well as the
        calibration coefficients defined in the report object.
        """
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        story.append(Spacer(1, 24))
        equ_text = "<font size=14>Calibration Equation</font>"
        story.append(Paragraph(equ_text, styles["Normal"]))
        story.append(Spacer(1, 10))


        equ_image = Image("database/placeholders/"\
                          "calibration_equation.png")
        story.append(equ_image)
        story.append(Spacer(1, 24))

        pix_text = "<font size=14>Where <b>p</b> is pixel index and:</font>"
        story.append(Paragraph(pix_text, styles["Normal"]))
        story.append(Spacer(1, 14))

        coeff_text = "<font size=14><b>C0=</b> %s</font>" \
                     % report.coeff_0
        story.append(Paragraph(coeff_text, styles["Normal"]))
        story.append(Spacer(1, 14))

        coeff_text = "<font size=14><b>C1=</b> %s</font>" \
                     % report.coeff_1
        story.append(Paragraph(coeff_text, styles["Normal"]))
        story.append(Spacer(1, 14))

        coeff_text = "<font size=14><b>C2=</b> %s</font>" \
                     % report.coeff_2
        story.append(Paragraph(coeff_text, styles["Normal"]))
        story.append(Spacer(1, 14))

        coeff_text = "<font size=14><b>C3=</b> %s</font>" \
                     % report.coeff_3
        story.append(Paragraph(coeff_text, styles["Normal"]))
        story.append(Spacer(1, 14))

    def add_images(self, story, report):
        """ Load the images as defined by the report filename side by
        side directly under the calibration header information.
        """

        orig_image0_filename = report.image0
        orig_image1_filename = report.image1

        # Resize the images with wand first so they will fit in the
        # table style scale height to 150px and preserve aspect ratio
        image0_filename = "temp_image0.png"
        image1_filename = "temp_image1.png"
        with WandImage(filename=orig_image0_filename) as img:
            img.transform(resize="x150")
            img.save(filename=image0_filename)

        with WandImage(filename=orig_image1_filename) as img:
            img.transform(resize="x150")
            img.save(filename=image1_filename)

        #log.info("PDFGen load: %s", image0_filename)
        left_img = Image(image0_filename)

        #log.info("PDFGen load: %s", image1_filename)
        right_img = Image(image1_filename)
        table_data = [[left_img, right_img]]

        edge_color = colors.white
        table = Table(table_data)
        in_grid = ("INNERGRID", (0, 0), (-1, -1), 0.25, edge_color)
        box = ("BOX", (0, 0), (-1, -1), 0.25, edge_color)
        back = ("BACKGROUND", (0, 0), (-1, 2), colors.white)
        table_style = TableStyle([in_grid, box, back])
        table.setStyle(table_style)

        story.append(table)

    def add_header(self, story, report):
        """ Insert the logo and top level text into the reportlab pdf
        story.
        """
        logo_filename = "database/placeholders/"\
                        "Wasatch_Photonics_logo_new.png"

        logo_img = Image(logo_filename, width=300, height=92)
        story.append(logo_img)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        story.append(Spacer(1, 12))
        serial_text = "<b>%s</b>" % report.serial
        title_text = "<font size=14>Calibration Report: %s</font>" \
                     % serial_text
        story.append(Paragraph(title_text, styles["Normal"]))
        story.append(Spacer(1, 12))

        timestamp = time.ctime()
        info_text = "Calibrated by: Auto Generated on %s" \
                    % timestamp

        story.append(Paragraph(info_text, styles["Normal"]))
        story.append(Spacer(1, 12))

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
