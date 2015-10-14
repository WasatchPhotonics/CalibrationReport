""" pdfgenerator - classes for using reportlab to generate wasatch
photonics specific calibration reports.
"""
        
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from calibrationreport.views import EmptyReport

class PDFGenerator(object):
    """ Generate a wasatch photoncis themed calibration report by
    default. All parameters are optional.
    """
    def __init__(self, filename="default.pdf", report=None,
                 header_image="WP_logo.png"):

        # Populate the report object with defaults if not specified
        if report is None:
            report = EmptyReport()
            
        doc = SimpleDocTemplate(filename, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        story = []
         
        self.add_header(story, report)
        doc.build(story)

    def add_header(self, story, report):
        """ Insert the logo and top level text into the reportlab pdf
        story.
        """
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        ser_text = '<font size=14><b>' + str(report.serial) + \
                    '</b></font>'

        story.append(Spacer(1, 12))
        ptext = '<font size=14>Calibration Report: </font>' + ser_text
        story.append(Paragraph(ptext, styles["Normal"]))
        story.append(Spacer(1, 12))

