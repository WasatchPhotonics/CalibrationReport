import os
import sys
import shutil
import logging
import unittest
import transaction

from pyramid import testing

from webtest import TestApp, Upload


log = logging.getLogger()                                                             
log.setLevel(logging.DEBUG)                                                           
                                                                                      
strm = logging.StreamHandler(sys.stderr)                                              
frmt = logging.Formatter("%(name)s - %(levelname)s %(message)s")                      
strm.setFormatter(frmt)                                                               
log.addHandler(strm)    


def register_routes(config):
    """ match the configuration in __init__ (a pyramid tutorials
    convention), to allow the unit tests to use the routes.
    """
    config.add_route("top_thumbnail", "top_thumbnail/{serial}")
    config.add_route("mosaic_thumbnail", "mosaic_thumbnail/{serial}")


class MockStorage(object):
    """ Create a storage object that references a file for use in
    view unittests.
    """
    def __init__(self, source_file_name):
        prefix = "database/placeholders"
        self.filename = "%s/%s" % (prefix, source_file_name)
        log.info("file: %s", self.filename)
        self.file = file(self.filename)

class TestPDFGenerator(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_all_options_unrequired(self):
        # when creating a pdf generator object, the files is written to
        # disk
        filename = "default.pdf"
        if os.path.exists(filename):
            os.remove(filename) 

        self.assertFalse(os.path.exists(filename)) 

        from calibrationreport.pdfgenerator import PDFGenerator
        pdf = PDFGenerator()

        self.assertTrue(os.path.exists(filename)) 

    def test_filename_specified(self):
        filename = "pdf_check.pdf"
        if os.path.exists(filename):
            os.remove(filename) 

        self.assertFalse(os.path.exists(filename)) 

        from calibrationreport.pdfgenerator import PDFGenerator
        pdf = PDFGenerator(filename=filename)

        self.assertTrue(os.path.exists(filename)) 
        

class TestCalibrationReportViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        register_routes(self.config)

    def tearDown(self):
        testing.tearDown()

    def test_home_empty_view_not_submitted(self):
        # Make sure serial number and all other fields are pre-populated
        # with defaults
        from calibrationreport.views import CalibrationReportViews
        request = testing.DummyRequest()
        inst = CalibrationReportViews(request)
        result = inst.cal_report()["fields"]

        self.assertEqual(result.serial, "unspecified")
        self.assertEqual(result.coeff_0, "0")
        self.assertEqual(result.coeff_1, "0")
        self.assertEqual(result.coeff_2, "0")
        self.assertEqual(result.coeff_3, "0")
        self.assertEqual(result.image0, "placeholder")
        self.assertEqual(result.image1, "placeholder")

    def test_home_view_submitted(self):
        # Populate a POST entry, verify the returned fields are
        # populated with the submitted entries
        from calibrationreport.views import CalibrationReportViews

        serial = "CRTEST123" # slug-friendly serial
        pdf_directory = "database/%s" % serial
        try:
            shutil.rmtree(pdf_directory)
        except OSError, e:
            log.exception(e)


        image0_store = MockStorage("image0_placeholder.jpg")
        image1_store = MockStorage("image1_placeholder.jpg")
        new_dict = {"form.submitted":"True", "serial":serial,
                    "coeff_0":"100", "coeff_1":"101", "coeff_2":"102",
                    "coeff_3":"103", 
                    "image0_file_content":image0_store,
                    "image1_file_content":image1_store}
    
        request = testing.DummyRequest(new_dict)
        inst = CalibrationReportViews(request)
        result = inst.cal_report()["fields"]

        self.assertEqual(result.serial, new_dict["serial"])
        self.assertEqual(result.coeff_0, new_dict["coeff_0"])
        self.assertEqual(result.coeff_1, new_dict["coeff_1"])
        self.assertEqual(result.coeff_2, new_dict["coeff_2"])
        self.assertEqual(result.coeff_3, new_dict["coeff_3"])
        self.assertEqual(result.image0,
                         new_dict["image0_file_content"].filename)
        self.assertEqual(result.image1,
                         new_dict["image1_file_content"].filename)
       
    def test_home_view_submitted_generates_pdf(self):
        # submit the post entry, verify that the pdf file is generated
        # on disk
        from calibrationreport.views import CalibrationReportViews

        # Delete the test file if it exists
        serial = "CRTEST123" # slug-friendly serial
        pdf_directory = "database/%s" % serial
        try:
            shutil.rmtree(pdf_directory)
        except OSError, e:
            log.exception(e)

        # Generate a post request
        image0_store = MockStorage("image0_placeholder.jpg")
        image1_store = MockStorage("image1_placeholder.jpg")
        new_dict = {"form.submitted":"True", "serial":serial,
                    "coeff_0":"100", "coeff_1":"101", "coeff_2":"102",
                    "coeff_3":"103", 
                    "image0_file_content":image0_store,
                    "image1_file_content":image1_store}
    
        request = testing.DummyRequest(new_dict)
        inst = CalibrationReportViews(request)
        result = inst.cal_report()
        links = result["links"]

        # Verify the file described in the links dict exists
        linked_file = "database/%s" % links["pdf_link"]
        self.assertTrue(os.path.exists(linked_file))

        # PDF generation is indeterminate file size, apparently because
        # of timestamps in the file. Set a range of +- N bytes to try
        # and compensate
        file_size = os.path.getsize(linked_file)
        base_size = 1720
        deviation = 50
        max_size = base_size + deviation
        min_size = base_size - deviation
        self.assertLess(file_size, max_size)
        self.assertGreater(file_size, min_size)

class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from calibrationreport import main
        settings = {}
        app = main({}, **settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        del self.testapp

    def test_home_form_starts_prepopulated(self):
        res = self.testapp.get("/")
        self.assertEqual(res.status_code, 200)
        #log.info("Body: %s", res.body)
        form = res.forms["cal_form"]
        self.assertEqual(form["serial"].value, "unspecified")
        self.assertEqual(form["coeff_0"].value, "0")
        self.assertEqual(form["coeff_1"].value, "0")
        self.assertEqual(form["coeff_2"].value, "0")
        self.assertEqual(form["coeff_3"].value, "0")

        # Apparently you can't access that "No file chosen" message, use
        # a separate field to mimic the last file uploaded. 
        # https://snakeycode.wordpress.com/2015/05/05/\
        # django-filefield-and-invalid-forms/
        self.assertTrue("Image0 File: placeholder" in res.body)
        self.assertTrue("Image1 File: placeholder" in res.body)
        

