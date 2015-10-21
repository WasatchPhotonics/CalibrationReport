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
        filename = "resources/example_qr_label.png"
        # Too small with default range 50
        self.assertFalse(file_range(filename, 30000))
        # Too big
        self.assertFalse(file_range(filename, 33000))

class TestPDFGenerator(unittest.TestCase):
    def test_all_options_unrequired(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "default.pdf"
        self.assertFalse(touch_erase(filename))
        pdf = WasatchSinglePage()
        self.assertTrue(file_range(filename, 186783, ok_range=5000))

    def test_filename_and_report_object_specified(self):
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "pdf_check.pdf"
        self.assertFalse(touch_erase(filename))
        pdf = WasatchSinglePage(filename=filename)
        self.assertTrue(file_range(filename, 186783, ok_range=5000))

    def test_fully_valid_report(self):
        from calibrationreport.models import EmptyReport
        from calibrationreport.pdfgenerator import WasatchSinglePage 

        filename = "with_images_check.pdf"
        self.assertFalse(touch_erase(filename))

        img0 = "reports/placeholders/image0_defined.jpg"
        img1 = "reports/placeholders/image1_defined.jpg"

        report = EmptyReport()
        report.serial = "DEFINEDSERIAL01234"
        report.image0 = img0
        report.image1 = img1
        report.coeff_0 = "1000.1213123*e-06"
        report.coeff_1 = "1001.1213123*e-06"
        report.coeff_2 = "1002.1213123*e-06"
        report.coeff_3 = "1003.1213123*e-06"
        pdf = WasatchSinglePage(filename=filename, report=report)
        self.assertTrue(file_range(filename, 106350))

    def test_thumbnail_generation(self):
        # Create the default report
        from calibrationreport.pdfgenerator import WasatchSinglePage
        filename = "default.pdf"
        self.assertFalse(touch_erase(filename))
        pdf = WasatchSinglePage()
        self.assertTrue(file_range(filename, 186783, ok_range=5000))

        # Generate the thumbnail of the first page
        png_filename = pdf.write_thumbnail()

        # Verify the size is as epected
        self.assertTrue(file_range(png_filename, 423808, ok_range=40000))

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
            dir_out = "label_files/%s" % slugify(item)
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
        self.assertEqual(data.top_image_filename, "top_blank")
        self.assertEqual(data.bottom_image_filename, "bottom_blank")

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
        self.assertEqual(data.top_image_filename, top_img_file)
        self.assertEqual(data.bottom_image_filename, bottom_img_file)

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
   
        
    def test_post_generates_pdf_file_on_disk(self):
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

        pdf_filename = "reports/%s/report.pdf" \
                       % slugify(post_dict["serial"])

        self.assertTrue(file_range(pdf_filename, 100000))

            
    def test_view_pdf(self):
        from calibrationreport.views import CalibrationReportViews

        known_pdf = "reports/placeholders/known_view.pdf"
        serial = "vt0001" # slug-friendly
        dest_dir = "reports/%s" % serial
        self.clean_directory(dest_dir)
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
    
        # Attempt to get a known invalid thumbnail filename, expect the
        # placeholder
        request = testing.DummyRequest()
        request.matchdict["serial"] = "knownbad01"
        inst = CalibrationReportViews(request)
        result = inst.view_thumbnail()

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_length, 4197)

    def test_view_thumbnail_known(self):
        from calibrationreport.views import CalibrationReportViews
        # manually copy a png placeholder into a known location, verify
        # the view can send it back
        known_png = "reports/placeholders/known_thumbnail.png"
        serial = "vt0001" # slug-friendly
        dest_dir = "reports/%s" % serial
        self.clean_directory(dest_dir)
        os.makedirs(dest_dir)
        shutil.copy(known_png, "%s/thumbnail.png" % dest_dir)

        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = CalibrationReportViews(request)
        result = inst.view_thumbnail()
        
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.content_length, 4197)
        
    def test_home_empty_view_not_submitted(self):
        from calibrationreport.views import CalibrationReportViews
        # Make sure serial number and all other fields are pre-populated
        # with defaults
        request = testing.DummyRequest()
        inst = CalibrationReportViews(request)
        result = inst.cal_report()["fields"]

        self.assertEqual(result.serial, "unspecified")
        self.assertEqual(result.coeff_0, "0")
        self.assertEqual(result.coeff_1, "0")
        self.assertEqual(result.coeff_2, "0")
        self.assertEqual(result.coeff_3, "0")
            
        expect_file0 = "reports/placeholders/image0_placeholder.jpg"
        self.assertEqual(result.image0, expect_file0)

        expect_file1 = "reports/placeholders/image1_placeholder.jpg"
        self.assertEqual(result.image1, expect_file1)

        images = inst.cal_report()["images"]
        self.assertEqual(images["thumbnail"], "unspecified/report.png")

    def clean_directory(self, dir_name):
        """ Helper function to ensure that the working directory is
        deleted and then recreated.
        """
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
       
    def test_home_view_invalid_posts(self):
        from calibrationreport.views import CalibrationReportViews
        # Populate a POST entry with invalid fields, verify that the
        # defaults are returned

        # empty storage fields
        new_dict = {"form.submitted":"True", "serial":"invtest1234",
                    "coeff_0":"100", "coeff_1":"101", "coeff_2":"102",
                    "coeff_3":"103",
                    "image0_file_content":"",
                    "image1_file_content":""}

        request = testing.DummyRequest(new_dict)
        inst = CalibrationReportViews(request)
        result = inst.cal_report()["fields"]
        self.assertEqual(result.serial, new_dict["serial"])

        expect_img0 = "reports/%s/image0.png" % new_dict["serial"]
        self.assertEqual(result.image0, expect_img0)
            
 
    def test_home_view_submitted(self):
        from calibrationreport.views import CalibrationReportViews
        # Populate a POST entry, verify the returned fields are
        # populated with the submitted entries. Don't check the pdf
        # status, just the population of the form 

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

        # When submitting an entry, expect the new hardcoded filename
        # for the uploaded imagery
        self.assertEqual(result.image0,
                         "reports/crtest1234/image0.png")
        self.assertEqual(result.image1,
                         "reports/crtest1234/image1.png")

        images = inst.cal_report()["images"]
        self.assertEqual(images["thumbnail"], 
                         "%s/report.png" % new_dict["serial"])
       
    def test_home_view_submitted_generates_pdf(self):
        # submit the post entry, verify that the pdf file is generated
        # on disk
        from calibrationreport.views import CalibrationReportViews

        # Delete the test file if it exists
        serial = "crtest456" # slug-friendly serial
        pdf_directory = "reports/%s" % serial
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
        linked_file = "reports/%s" % links["pdf_link"]
        self.assertTrue(os.path.exists(linked_file))

        # PDF generation is indeterminate file size, apparently because
        # of timestamps in the file. Set a range of +- N bytes to try
        # and compensate
        self.assertTrue(file_range(linked_file, 186789, ok_range=5000))

        # Make sure the thumbnail image exists and is within file size
        img_file = "reports/%s" % result["images"]["thumbnail"]
        print "actual size is: %s" % (os.path.getsize(img_file))
        log.warn("warn size is: %s" % (os.path.getsize(img_file)))
        self.assertTrue(file_range(img_file, 423808, ok_range=40000))


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

        match_img = "src=\"/view_thumbnail"
        self.assertTrue(match_img in res.body)

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

        # Submitting via an actual browser strips the directory
        # prefixes. Copy the files to temporary locations to exactly
        # mimic this
        image0_file = "reports/placeholders/image0_defined.jpg"
        image1_file = "reports/placeholders/image1_defined.jpg"
        shutil.copy(image0_file, "localimg0.jpg")
        shutil.copy(image1_file, "localimg1.jpg")

        form["image0_file_content"] = Upload("localimg0.jpg")
        form["image1_file_content"] = Upload("localimg1.jpg")


        submit_res = form.submit("form.submitted")

        # Get the new form, make sure the fields are populated as
        # expected
        new_form = submit_res.forms["cal_form"]
        #log.info("Full submit res %s", submit_res)
        self.assertEqual(new_form["serial"].value, "ft789")
        self.assertEqual(new_form["coeff_0"].value, "200.9892*e-07")
        self.assertEqual(new_form["coeff_1"].value, "201.9892*e-07")
        self.assertEqual(new_form["coeff_2"].value, "202.9892*e-07")
        self.assertEqual(new_form["coeff_3"].value, "203.9892*e-07")

        # The files are uploaded and hardcoded to filename: image0 and
        # image1.png regardless of their format. Expect this hardcoded
        # filename returned
        self.assertTrue("reports/ft789/image0.png" in submit_res.body)
        self.assertTrue("reports/ft789/image1.png" in submit_res.body)

        # Click pdf link, follow it and make sure it is the right size
        click_res = submit_res.click(linkid="pdf_link") 

        # See the unit test code above for why this is necessary
        size_range(click_res.content_length, 106338, ok_range=5000)

        # Cleanup the temp files - after the request has completed!
        os.remove("localimg0.jpg")
        os.remove("localimg1.jpg")

