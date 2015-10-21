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

from coverageutils import file_range, touch_erase, size_range

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
        self.assertFalse(file_range(filename, 63000))
        # Too big
        self.assertFalse(file_range(filename, 62000))

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
        self.assertTrue(file_range(filename, 106311))

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
        self.assertTrue(file_range(png_filename, 198863, ok_range=40000))

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

    def test_get_returns_default_form(self):
        from calibrationreport.views import CalibrationReportViews

        request = testing.DummyRequest()
        inst = CalibrationReportViews(request)
        result = inst.calibration_report()

        data = result["data"]
        self.assertEqual(data.serial, "")
        self.assertEqual(data.coefficient_0, "")
        self.assertEqual(data.coefficient_1, "")
        self.assertEqual(data.coefficient_2, "")
        self.assertEqual(data.coefficient_3, "")
        self.assertEqual(data.top_image_filename, "")
        self.assertEqual(data.bottom_image_filename, "")

    def test_post_completed_form_no_images_returns_populated(self):
        from calibrationreport.views import CalibrationReportViews
        post_dict = {"submit":"submit", "serial":"UT5555",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103"}

        request = testing.DummyRequest(post_dict)
        inst = CalibrationReportViews(request)
        result = inst.calibration_report()

        data = result["data"]
        self.assertEqual(data.serial, post_dict["serial"])
        self.assertEqual(data.coefficient_0, post_dict["coefficient_0"])
        self.assertEqual(data.coefficient_1, post_dict["coefficient_1"])
        self.assertEqual(data.coefficient_2, post_dict["coefficient_2"])
        self.assertEqual(data.coefficient_3, post_dict["coefficient_3"])
        
    def test_post_completed_form_with_images_returns_populated(self):
        from calibrationreport.views import CalibrationReportViews
      
        top_img_file = "resources/image0_defined.jpg" 
        bottom_img_file = "resources/image1_defined.jpg" 
        top_img = DeformMockFieldStorage(top_img_file)
        bottom_img = DeformMockFieldStorage(bottom_img_file)
   
        top_upload_dict = {"upload":top_img}
        bottom_upload_dict = {"upload":bottom_img}
 
        post_dict = {"submit":"submit", "serial":"UT5555",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103",
                     "top_image_upload":top_upload_dict,
                     "bottom_image_upload":bottom_upload_dict}

        request = testing.DummyRequest(post_dict)
        inst = CalibrationReportViews(request)
        result = inst.calibration_report()

        data = result["data"]
        self.assertEqual(data.serial, post_dict["serial"])
        self.assertEqual(data.coefficient_0, post_dict["coefficient_0"])
        self.assertEqual(data.coefficient_1, post_dict["coefficient_1"])
        self.assertEqual(data.coefficient_2, post_dict["coefficient_2"])
        self.assertEqual(data.coefficient_3, post_dict["coefficient_3"])

        # When images are uploaded, the hardcoded filenames are used.
        # Verify that they have been overwritten in the data filename
        # fields
        slugged = slugify(post_dict["serial"])
        self.assertEqual(data.top_image_filename, 
                         "reports/%s/top_image.png" % slugged)
        self.assertEqual(data.bottom_image_filename, 
                         "reports/%s/bottom_image.png" % slugged)

    def test_invalid_serial_coefficients_rules_always_return_form(self):
        from calibrationreport.views import CalibrationReportViews
    
        # The deform library handles the user feedback on field
        # requirements. Populate a POST request with known invalid data
        # for the various fields, make sure they are reset to the
        # default blanks where applicable.
        post_dict = {"submit":"submit", 
                     "serial":"", # blank serial disallowed
                     "coefficient_0":"", 
                     "coefficient_1":"", 
                     "coefficient_2":"", 
                     "coefficient_3":"103waytoolongforacoefficienttex",}

        request = testing.DummyRequest(post_dict)
        inst = CalibrationReportViews(request)
        result = inst.calibration_report()

        data = result["data"]
        self.assertEqual(data.serial, post_dict["serial"])
        self.assertEqual(data.coefficient_0, post_dict["coefficient_0"])
        self.assertEqual(data.coefficient_1, post_dict["coefficient_1"])
        self.assertEqual(data.coefficient_2, post_dict["coefficient_2"])
        self.assertEqual(data.coefficient_3, "")
        
    def test_post_generates_pdf_and_png_files_on_disk(self):
        from calibrationreport.views import CalibrationReportViews
      
        top_img_file = "resources/top_image_785l.jpg" 
        bottom_img_file = "resources/bottom_image_785l.jpg" 
        top_img = DeformMockFieldStorage(top_img_file)
        bottom_img = DeformMockFieldStorage(bottom_img_file)
   
        top_upload_dict = {"upload":top_img}
        bottom_upload_dict = {"upload":bottom_img}
 
        post_dict = {"submit":"submit", "serial":"UT5555",
                     "coefficient_0":"100", "coefficient_1":"101", 
                     "coefficient_2":"102", "coefficient_3":"103",
                     "top_image_upload":top_upload_dict,
                     "bottom_image_upload":bottom_upload_dict}

        request = testing.DummyRequest(post_dict)
        inst = CalibrationReportViews(request)
        result = inst.calibration_report()

        pdf_filename = "reports/%s/report.pdf" \
                       % slugify(post_dict["serial"])
        self.assertTrue(file_range(pdf_filename, 115746, ok_range=20000))

        png_thumb = "reports/%s/report.png" \
                    % slugify(post_dict["serial"])
        self.assertTrue(file_range(png_thumb, 233994, ok_range=40000))

            
    def test_view_existing_pdf(self):
        from calibrationreport.views import CalibrationReportViews

        known_pdf = "resources/known_report.pdf"
        serial = "ut0001" # slug-friendly
        dest_dir = "reports/%s" % serial
        os.makedirs(dest_dir)
        shutil.copy(known_pdf, "%s/report.pdf" % dest_dir)

        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = CalibrationReportViews(request)
        result = inst.view_pdf()
        
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_length, 208628)

    def test_view_thumbnail_unknown(self):
        from calibrationreport.views import CalibrationReportViews
    
        request = testing.DummyRequest()
        request.matchdict["serial"] = "knownbad01"
        inst = CalibrationReportViews(request)
        result = inst.view_thumbnail()

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_length, 4197)

    def test_view_thumbnail_known(self):
        from calibrationreport.views import CalibrationReportViews
        
        known_png = "resources/known_thumbnail.png"
        serial = "ut0001" # slug-friendly
        dest_dir = "reports/%s" % serial
        os.makedirs(dest_dir)
        shutil.copy(known_png, "%s/thumbnail.png" % dest_dir)

        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = CalibrationReportViews(request)
        result = inst.view_thumbnail()
        
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_length, 4197)
        
    def test_serialless_route_to_placeholder_thumbnail(self):
        from calibrationreport.views import CalibrationReportViews

        request = testing.DummyRequest()
        inst = CalibrationReportViews(request)
        result = inst.blank_thumbnail()
        
        self.assertEqual(result.content_length, 179243)

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
        test_serials = ["ft789"]

        for item in test_serials:
            dir_out = "reports/%s" % slugify(item)
            if os.path.exists(dir_out):
                shutil.rmtree(dir_out)

    def test_home_form_starts_prepopulated(self):
        res = self.testapp.get("/")
        self.assertEqual(res.status_code, 200)
        form = res.forms["deform"]
        self.assertEqual(form["serial"].value, "")
        self.assertEqual(form["coefficient_0"].value, "")
        self.assertEqual(form["coefficient_1"].value, "")
        self.assertEqual(form["coefficient_2"].value, "")
        self.assertEqual(form["coefficient_3"].value, "")

        match_img = "src=\"/view_thumbnail/"
        self.assertTrue(match_img in res.body)

        match_link = "href=\"/view_pdf/"
        self.assertTrue(match_link in res.body)

    def test_submit_and_follow_pdf_link(self):
        res = self.testapp.get("/")
        self.assertEqual(res.status_code, 200)
        #log.info("Body: %s", res.body)
        form = res.forms["deform"]
        form["serial"] = "ft789"
        form["coefficient_0"] = "200.9892*e-07"
        form["coefficient_1"] = "201.9892*e-07"
        form["coefficient_2"] = "202.9892*e-07"
        form["coefficient_3"] = "203.9892*e-07"

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
        # Get the new form, make sure the fields are populated as
        # expected
        new_form = submit_res.forms["deform"]
        #log.info("Full submit res %s", submit_res)
        self.assertEqual(new_form["serial"].value, "ft789")
        self.assertEqual(new_form["coefficient_0"].value, "200.9892*e-07")
        self.assertEqual(new_form["coefficient_1"].value, "201.9892*e-07")
        self.assertEqual(new_form["coefficient_2"].value, "202.9892*e-07")
        self.assertEqual(new_form["coefficient_3"].value, "203.9892*e-07")

        # Click pdf link, follow it and make sure it is the right size
        click_res = submit_res.click(linkid="pdf_link") 

        # See the unit test code above for why this is necessary
        size_range(click_res.content_length, 106338, ok_range=5000)

        # Cleanup the temp files - after the request has completed!
        os.remove("localimg0.jpg")
        os.remove("localimg1.jpg")

