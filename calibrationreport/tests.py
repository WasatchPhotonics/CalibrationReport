""" unit and functional tests for the calibrationreport application
"""
import os
import sys
import shutil
import logging
import unittest

from slugify import slugify

from pyramid import testing

from webtest import TestApp, Upload

from calibrationreport.coverageutils import file_range, touch_erase
from calibrationreport.coverageutils import size_range

log = logging.getLogger()
log.setLevel(logging.INFO)

# Specify stdout as the logging output stream to reduce verbosity in the
# nosetest output. This will let you still see all of logging when
# running with python -u -m unittest, yet swallow it all in nosetest.
strm = logging.StreamHandler(sys.stdout)
frmt = logging.Formatter("%(name)s - %(levelname)s %(message)s")
strm.setFormatter(frmt)
log.addHandler(strm)

class DeformMockFieldStorage(object):
    """ Create a storage object that references a file for use in
    view unittests. Deform/colander requires a dictionary to address the
    multiple upload fields. This is not required for 'plain' html file
    uploads.
    """
    def __init__(self, source_file_name):
        self.filename = source_file_name
        self.file = file(self.filename)
        self.type = "file"
        self.length = os.path.getsize(self.filename)

class TestCoverageUtils(unittest.TestCase):
    def test_file_does_not_exist(self):
        filename = "known_unknown_file"
        self.assertFalse(file_range(filename, 10000))

    def test_file_sizes_out_of_range(self):
        filename = "resources/image0_defined.jpg"
        # Too small with default range 50
        self.assertFalse(file_range(filename, 64000))
        # Too big
        self.assertFalse(file_range(filename, 61000))

class TestPDFGenerator(unittest.TestCase):
    def test_all_options_unrequired(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "default.pdf"
        self.assertFalse(touch_erase(filename))
        pdf = WasatchSinglePage()
        self.assertTrue(file_range(filename, 101200, ok_range=5000))

    def test_filename_and_report_object_specified(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "pdf_check.pdf"
        self.assertFalse(touch_erase(filename))
        pdf = WasatchSinglePage(filename=filename)
        self.assertTrue(file_range(filename, 101200, ok_range=5000))

    def test_fully_valid_report(self):
        from calibrationreport.models import EmptyReport
        from calibrationreport.pdfgenerator import WasatchSinglePage 

        filename = "with_images_check.pdf"
        self.assertFalse(touch_erase(filename))

        img0 = "resources/image0_defined.jpg"
        img1 = "resources/image1_defined.jpg"

        report = EmptyReport()
        report.serial = "DEFINEDSERIAL01234"
        report.coeff_0 = "1000.1213123*e-06"
        report.coeff_1 = "1001.1213123*e-06"
        report.coeff_2 = "1002.1213123*e-06"
        report.coeff_3 = "1003.1213123*e-06"
        report.top_image_filename = img0
        report.bottom_image_filename = img1
        pdf = WasatchSinglePage(filename=filename, report=report)
        self.assertTrue(file_range(filename, 106494))

    def test_thumbnail_generation(self):
        # Create the default report
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "default.pdf"
        self.assertFalse(touch_erase(filename))
        pdf = WasatchSinglePage()
        self.assertTrue(file_range(filename, 101194, ok_range=5000))

        # Generate the thumbnail of the first page
        png_filename = pdf.write_thumbnail()

        # Verify the size is as epected
        self.assertTrue(file_range(png_filename, 198863, 
                                   ok_range=40000))

    def test_can_return_blob_main_pdf(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage

        pdf = WasatchSinglePage(return_blob=True)
        blob_data = pdf.return_blob()

        self.assertTrue(size_range(len(blob_data), 101194, ok_range=5000))
        
    def test_can_return_blob_thumbnail_from_pdf(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage

        pdf = WasatchSinglePage(return_blob=True)
        blob_data = pdf.return_thumbnail_blob()

        self.assertTrue(size_range(len(blob_data), 198863, 
                                   ok_range=40000))
        

class TestCalibrationReportViews(unittest.TestCase):
    def setUp(self):
        self.clean_test_files()
        self.config = testing.setUp()

    def tearDown(self):
        # Comment out this line for easier post-test state inspections
        #self.clean_test_files()
        testing.tearDown()

    def clean_test_files(self):
        # Remove the directory if it exists
        test_serials = ["FT1234", "UT5555", "UT0001"]

        for item in test_serials:
            dir_out = "reports/%s" % slugify(item)
            if os.path.exists(dir_out):
                shutil.rmtree(dir_out)

    def post_calibration_report(self, post_dict):
        """ Convenience function to post the supplied dictionary to the
        request.
        """
        from calibrationreport.views import CalibrationReportViews
        request = testing.DummyRequest(post_dict)
        inst = CalibrationReportViews(request)
        return inst.calibration_report()

    def test_get_returns_default_form(self):
        result = self.post_calibration_report(post_dict={})
        self.assertIsNone(result.get("appstruct"))

    def test_serial_missing_or_blank_is_failing(self):
        post_dict = {"submit":"submit", 
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103"}
        result = self.post_calibration_report(post_dict)
        self.assertIsNone(result.get("appstruct"))
        
        post_dict = {"submit":"submit", "serial":"",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103"}
        result = self.post_calibration_report(post_dict)
        self.assertIsNone(result.get("appstruct"))
       
    def test_coefficients_missing_or_blank_is_failing(self): 
        for item in ["0", "1", "2", "3"]:
            post_dict = {"submit":"submit", "serial":"UT5555",
                         "coefficient_0":"100", "coefficient_1":"101", 
                         "coefficient_2":"102", "coefficient_3":"103"}
            post_dict["coefficient_%s" % item] = ""
            result = self.post_calibration_report(post_dict)
            self.assertIsNone(result.get("appstruct"))

            del post_dict["coefficient_%s" % item]
            result = self.post_calibration_report(post_dict)
            self.assertIsNone(result.get("appstruct"))

    def test_completed_form_creates_hardcoded_filenames(self):
        post_dict = {"submit":"submit", "serial":"UT5555",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103"}
        result = self.post_calibration_report(post_dict)

        self.assertTrue(file_range("reports/ut5555/report.pdf", 106473,
                                   ok_range=40000))
        self.assertTrue(file_range("reports/ut5555/report.png", 220137,
                                   ok_range=40000))
       
      
    def test_completed_form_report_created_is_accessible(self):
        post_dict = {"submit":"submit", "serial":"UT5555",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103"}
        result = self.post_calibration_report(post_dict)

        from calibrationreport.views import CalibrationReportViews
        request = testing.DummyRequest()
        request.matchdict["serial"] = "ut5555"
        inst = CalibrationReportViews(request)
        result = inst.view_pdf() 
        self.assertTrue(size_range(result.content_length, 106473))
      
    def test_completed_form_thumbnail_created_is_accessible(self):
        post_dict = {"submit":"submit", "serial":"UT5555",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103"}
        result = self.post_calibration_report(post_dict)

        from calibrationreport.views import CalibrationReportViews
        request = testing.DummyRequest()
        request.matchdict["serial"] = "ut5555"
        inst = CalibrationReportViews(request)
        result = inst.view_thumbnail() 
        self.assertTrue(size_range(result.content_length, 220137,
                                   ok_range=40000))

class FunctionalTests(unittest.TestCase):
    def setUp(self):
        self.clean_test_files()
        from calibrationreport import main
        settings = {}
        app = main({}, **settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        # Uncomment this line for cleaner cleanup at the expense of
        # viewing failed files
        #self.clean_test_files()
        del self.testapp

    def clean_test_files(self):
        # Remove the directory if it exists
        dir_out = "reports/ft789"
        if os.path.exists(dir_out):
            shutil.rmtree(dir_out)

    def test_home_form_starts_empty_placeholders_visible(self):
        res = self.testapp.get("/")
        log.info("Full form: %s", res)
        self.assertEqual(res.status_code, 200)

        form = res.forms["deform"]
        self.assertEqual(form["serial"].value, "")

        indexed_form_name = form.get("upload", 0).name
        self.assertEqual(indexed_form_name, "upload")

        match_example = "assets/img/example_report_thumbnail.png"
        self.assertTrue(match_example in res.body)

    def test_imagery_placeholder_is_accessible(self):
        res = self.testapp.get("/assets/img/example_report_thumbnail.png")
        self.assertEqual(res.status_code, 200)

    def test_submit_with_no_values_has_error_messages(self):
        res = self.testapp.get("/")
        form = res.forms["deform"]
        submit_res = form.submit("submit")
        self.assertTrue("was a problem with your" in submit_res.body) 

    def test_submit_with_no_images_has_no_error_messages(self):
        res = self.testapp.get("/")
        form = res.forms["deform"]
        form["serial"] = "ft789"
        form["coefficient_0"] = "100"
        form["coefficient_1"] = "101"
        form["coefficient_2"] = "102"
        form["coefficient_3"] = "103"

        submit_res = form.submit("submit")
        self.assertTrue("was a problem with" not in submit_res.body)

    def test_submit_with_all_values_has_no_error_messages(self):
        res = self.testapp.get("/")
        form = res.forms["deform"]
        form["serial"] = "ft789"
        form["coefficient_0"] = "100"
        form["coefficient_1"] = "101"
        form["coefficient_2"] = "102"
        form["coefficient_3"] = "103"

        # Submitting via an actual browser strips the directory
        # prefixes. Copy the files to temporary locations to exactly
        # mimic this
        image0_file = "resources/image0_defined.jpg"
        image1_file = "resources/image1_defined.jpg"
        shutil.copy(image0_file, "localimg0.jpg")
        shutil.copy(image1_file, "localimg1.jpg")

        # From: # http://stackoverflow.com/questions/3337736/\
        # how-do-i-use-pylons-paste-webtest-with-multiple-\
        # checkboxes-with-the-same-name
        top_index = 0
        bottom_index = 1
        form.set("upload", Upload("localimg0.jpg"), top_index)
        form.set("upload", Upload("localimg1.jpg"), bottom_index)

        submit_res = form.submit("submit")
        self.assertTrue("was a problem with" not in submit_res.body)

    def test_submit_with_all_values_pdf_link_available(self):
        res = self.testapp.get("/")
        form = res.forms["deform"]
        form["serial"] = "ft789"
        form["coefficient_0"] = "100"
        form["coefficient_1"] = "101"
        form["coefficient_2"] = "102"
        form["coefficient_3"] = "103"

        submit_res = form.submit("submit")
        self.assertTrue("was a problem with" not in submit_res.body)

        pdf_link = "href=\"/view_pdf/ft789"
        self.assertTrue(pdf_link in submit_res.body)
 
        res = self.testapp.get("/view_pdf/ft789")
        img_size = res.content_length
        self.assertTrue(size_range(img_size, 106468, ok_range=5000))

    def test_submit_with_images_report_and_thumbnail_matches_size(self):
        res = self.testapp.get("/")
        form = res.forms["deform"]
        form["serial"] = "ft789"
        form["coefficient_0"] = "100"
        form["coefficient_1"] = "101"
        form["coefficient_2"] = "102"
        form["coefficient_3"] = "103"

        # Submitting via an actual browser strips the directory
        # prefixes. Copy the files to temporary locations to exactly
        # mimic this
        image0_file = "resources/image0_defined.jpg"
        image1_file = "resources/image1_defined.jpg"
        shutil.copy(image0_file, "localimg0.jpg")
        shutil.copy(image1_file, "localimg1.jpg")

        # From: # http://stackoverflow.com/questions/3337736/\
        # how-do-i-use-pylons-paste-webtest-with-multiple-\
        # checkboxes-with-the-same-name
        top_index = 0
        bottom_index = 1
        form.set("upload", Upload("localimg0.jpg"), top_index)
        form.set("upload", Upload("localimg1.jpg"), bottom_index)
        submit_res = form.submit("submit")

        res = self.testapp.get("/view_pdf/ft789")
        pdf_size = res.content_length
        self.assertTrue(size_range(pdf_size, 106456, ok_range=40000))

        res = self.testapp.get("/view_thumbnail/ft789")
        png_size = res.content_length
        self.assertTrue(size_range(png_size, 217477, ok_range=40000))
