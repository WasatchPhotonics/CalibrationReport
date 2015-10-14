""" WasatchSinglePage - classes for using reportlab to generate wasatch
photonics specific calibration reports.
"""

import time
import logging
        
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from calibrationreport.models import EmptyReport

log = logging.getLogger(__name__)

class WasatchSinglePage(object):
    """ Generate a wasatch photoncis themed calibration report by
    default. All parameters are optional.
    """
    def __init__(self, filename="default.pdf", report=None):

        # Populate the report object with defaults if not specified
        if report is None:
            report = EmptyReport()
            
        self.doc = SimpleDocTemplate(filename, pagesize=letter,
                                     rightMargin=72, leftMargin=72,
                                     topMargin=72, bottomMargin=18)

        story = []
        self.add_header(story, report)
        self.add_images(story, report)
        self.doc.build(story)

    def add_images(self, story, report):
        """ Load the images as defined by the report filename side by
        side directly under the calibration header information.
        """
       
        image0_filename = report.image0
        image1_filename = report.image1
    
        left_img = Image(image0_filename)
        left_img.drawHeight = 2*inch
        left_img.drawWidth = 2*inch
    
        right_img = Image(image1_filename)
        right_img.drawHeight = 2*inch
        right_img.drawWidth = 2*inch
        data=[[left_img, right_img]]
        
        edge_color = colors.black
        edge_color = colors.white
        #table = Table(data, colWidths=200, rowHeights=200)
        table = Table(data)
        table.setStyle(TableStyle([
                                ('INNERGRID', (0,0), (-1,-1), 0.25, edge_color),
                                ('BOX', (0,0), (-1,-1), 0.25, edge_color),
                                ('BACKGROUND',(0,0),(-1,2), colors.white)
                                ]))
        
        story.append(table)

    def add_header(self, story, report):
        """ Insert the logo and top level text into the reportlab pdf
        story.
        """
        logo_filename = "database/placeholders/"\
                        "Wasatch_Photonics_logo_new.png"
         
        logo_img  = Image(logo_filename, width=300, height=92)
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
         
         


