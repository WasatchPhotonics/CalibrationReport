""" unit and functional tests for the calibrationreport application
"""
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
    config.add_route("view_pdf", "view_pdf/{serial}")
    # why doon't you need to register routes?


    #


class MockStorage(object):
    """ Create a storage object that references a file for use in
    view unittests.
    """
    def __init__(self, source_file_name):
        prefix = "database/placeholders"
        self.filename = "%s/%s" % (prefix, source_file_name)
        self.file = file(self.filename)
        #log.info("Mock storage file: %s", self.filename)

class TestPDFGenerator(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_all_options_unrequired(self):
        # when creating a pdf generator object, the files is written to
        # disk
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "default.pdf"
        self.touch_then_erase(filename)
        pdf = WasatchSinglePage()
        self.exists_and_file_range(filename, base=649000)

    def exists_and_file_range(self, filename, base=1720, deviation=5000):
        """ Helper function to assert that a file exists, and it's size
        is within the expected range. PDF's generated within seconds of
        each other with identical settings have different sizes with
        reportlab.
        """
        self.assertTrue(os.path.exists(filename)) 

        file_size = os.path.getsize(filename)
        max_size = base + deviation
        min_size = base - deviation
        self.assertLess(file_size, max_size)
        self.assertGreater(file_size, min_size)

    def test_filename_and_report_object_specified(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "pdf_check.pdf"
        self.touch_then_erase(filename)
        pdf = WasatchSinglePage(filename=filename)
        self.exists_and_file_range(filename=filename, base=649000)

    def touch_then_erase(self, filename):
        """ Helper function to erase a file if it exists. Touches the
        file first so coverage is always 100%
        """
        # http://stackoverflow.com/questions/12654772/\
        # create-empty-file-using-python
        open(filename, 'a').close()
        if os.path.exists(filename):
            os.remove(filename) 
        self.assertFalse(os.path.exists(filename)) 

       
    def test_fully_valid_report(self):
        from calibrationreport.models import EmptyReport
        from calibrationreport.pdfgenerator import WasatchSinglePage 

        filename = "with_images_check.pdf"
        self.touch_then_erase(filename)

        img0 = "database/placeholders/image0_defined.jpg"
        img1 = "database/placeholders/image1_defined.jpg"

        report = EmptyReport()
        report.serial = "DEFINEDSERIAL01234"
        report.image0 = img0
        report.image1 = img1
        report.coeff_0 = "1000.1213123*e-06"
        report.coeff_1 = "1001.1213123*e-06"
        report.coeff_2 = "1002.1213123*e-06"
        report.coeff_3 = "1003.1213123*e-06"
        pdf = WasatchSinglePage(filename=filename, report=report)
        self.exists_and_file_range(filename=filename, base=208000)


class TestCalibrationReportViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        #register_routes(self.config)

    def tearDown(self):
        testing.tearDown()

    def test_view_pdf(self):
        # manually copy a pdf placeholder into a known location, verify
        # the view can send it back
        known_pdf = "database/placeholders/known_view.pdf"
        serial = "vt0001" # slug-friendly
        dest_dir = "database/%s" % serial
        self.clean_directory(dest_dir)
        os.makedirs(dest_dir)
        shutil.copy(known_pdf, "%s/report.pdf" % dest_dir)

        from calibrationreport.views import CalibrationReportViews
        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = CalibrationReportViews(request)
        result = inst.view_pdf()
        
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_length, 208628)

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
        self.assertEqual(result.image0, 
            "database/placeholders/image0_placeholder.jpg")
        self.assertEqual(result.image1, 
            "database/placeholders/image1_placeholder.jpg")

    def clean_directory(self, dir_name):
        """ Helper function to ensure that the working directory is
        deleted and then recreated.
        """
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
        
    def test_home_view_submitted(self):
        # Populate a POST entry, verify the returned fields are
        # populated with the submitted entries. Don't check the pdf
        # status, just the population of the form 
        from calibrationreport.views import CalibrationReportViews

        image0_store = MockStorage("image0_placeholder.jpg")
        image1_store = MockStorage("image1_placeholder.jpg")
        new_dict = {"form.submitted":"True", "serial":"crtest1234",
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
        serial = "crtest456" # slug-friendly serial
        pdf_directory = "database/%s" % serial
        self.clean_directory(pdf_directory)

        # Generate a post request. These mock data storage filenames
        # happen to be the same as what the pdf generator will use if
        # not specified
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
        base_size = 649000
        deviation = 5000
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
        self.assertTrue("image0_placeholder.jpg" in res.body)
        self.assertTrue("image1_placeholder.jpg" in res.body)

    def test_submit_and_follow_pdf_link(self):
        res = self.testapp.get("/")
        self.assertEqual(res.status_code, 200)
        #log.info("Body: %s", res.body)
        form = res.forms["cal_form"]
        form["serial"] = "ft789"
        form["coeff_0"] = "200.9892*e-07"
        form["coeff_1"] = "201.9892*e-07"
        form["coeff_2"] = "202.9892*e-07"
        form["coeff_3"] = "203.9892*e-07"

        image0_file = "database/placeholders/image0_defined.jpg"
        image1_file = "database/placeholders/image1_defined.jpg"
        form["image0_file_content"] = Upload(image0_file) 
        form["image1_file_content"] = Upload(image1_file) 

        submit_res = form.submit("form.submitted")

        # Get the new form, make sure the fields are populated as
        # expected
        new_form = submit_res.forms["cal_form"]
        self.assertEqual(new_form["serial"].value, "ft789")
        self.assertEqual(new_form["coeff_0"].value, "200.9892*e-07")
        self.assertEqual(new_form["coeff_1"].value, "201.9892*e-07")
        self.assertEqual(new_form["coeff_2"].value, "202.9892*e-07")
        self.assertEqual(new_form["coeff_3"].value, "203.9892*e-07")
        self.assertTrue("image0_defined.jpg" in submit_res.body)
        self.assertTrue("image1_defined.jpg" in submit_res.body)

        # Click pdf link, follow it and make sure it is the right size
        click_res = submit_res.click(linkid="pdf_link") 
        self.assertEqual(click_res.content_length, 208628)

