""" datamodel objects used by the calibrationreport project.
"""

class EmptyReport(object):
    """ Helper class for empty calibration report population.
    """
    serial = "unspecified"
    coeff_0 = "0"
    coeff_1 = "0"
    coeff_2 = "0"
    coeff_3 = "0"
    image0 = "reports/placeholders/image0_placeholder.jpg"
    image1 = "reports/placeholders/image1_placeholder.jpg"
