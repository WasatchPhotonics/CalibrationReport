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
    config.add_route("home_view", "/")
    config.add_route("top_thumbnail", "top_thumbnail/{serial}")
    config.add_route("mosaic_thumbnail", "mosaic_thumbnail/{serial}")

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
        self.assertEqual(result.coeff_0, "unspecified")
        

class TestThumbnailViews(unittest.TestCase):
    def setUp(self):
        # Clean any existing test files
        self.clean_test_files()
        self.config = testing.setUp()
        register_routes(self.config)

    def tearDown(self):
        # Comment out this line for easier post-test state inspections
        self.clean_test_files()
        testing.tearDown()

    def clean_test_files(self):
        # Remove the directory if it exists
        dir_out = "database/imagery/test0123"
        if os.path.exists(dir_out):
            result = shutil.rmtree(dir_out)
            self.assertIsNone(result)

        dir_out = "database/imagery/functest1234"
        if os.path.exists(dir_out):
            result = shutil.rmtree(dir_out)
            self.assertIsNone(result)
 
    def test_bad_submit_pdf(self):
        # upload various stages of incomplete form, make sure it fails
        # according to business rules
        from calibrationreport.views import ThumbnailViews

        # Get the add pdf view, verify that the form fields are
        # available
        request = testing.DummyRequest()
        inst = ThumbnailViews(request)
        view_back = inst.add_pdf()

        # Verify that the form fields are available
        self.assertEqual(view_back["serial"], "") 
        self.assertEqual(view_back["filename"], "")

        # Attempt to submit without specifying a serial number field,
        # expect a failure
        new_dict = {"form.submitted":"True"}
        request = testing.DummyRequest(new_dict)
        inst = ThumbnailViews(request)
        view_back = inst.add_pdf()
        self.assertEqual(view_back.status_code, 404)
       
        # Attempt submit specifying blank serial 
        new_dict = {"form.submitted":"True", "serial":""}
        request = testing.DummyRequest(new_dict)
        inst = ThumbnailViews(request)
        view_back = inst.add_pdf()
        self.assertEqual(view_back.status_code, 404)

    def test_add_thumbnails_from_pdf(self):
        from calibrationreport.views import ThumbnailViews
        # Specify a file object, submit it to the view
        serial = "test0123" # slug-friendly serial
        source_file_name = "database/imagery/work_ticket_test.pdf"

        # From:  http://stackoverflow.com/questions/11102432/\
        # pyramid-writing-unittest-for-file-upload-for
        class MockStorage(object):
            log.info("file: %s", source_file_name)
            file = file(source_file_name)
            filename = source_file_name

        new_dict = {"form.submitted":"True", "serial":serial,
                    "file_content":MockStorage()}

        request = testing.DummyRequest(new_dict)
        inst = ThumbnailViews(request)
        view_back = inst.add_pdf()
        self.assertEqual(view_back["serial"], serial)
        self.assertEqual(view_back["filename"], source_file_name)

        # Call the display view and verify the top page thumbnail has
        # been generated
        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = ThumbnailViews(request)
        view_back = inst.top_thumbnail()

        dest_file_name = "database/imagery/test0123/top_thumbnail.png"
        actual_size = os.path.getsize(dest_file_name)
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

        # Now verify the mosaic thumbnail has been generated
        dest_file_name = "database/imagery/test0123/mosaic_thumbnail.png"
        view_back = inst.mosaic_thumbnail()
        actual_size = os.path.getsize(dest_file_name)
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

        # Run it again to ensure that the mosaic tiles are deleted
        log.info("About to call again")
        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = ThumbnailViews(request)

        dest_file_name = "database/imagery/test0123/mosaic_thumbnail.png"
        view_back = inst.mosaic_thumbnail()
        actual_size = os.path.getsize(dest_file_name)
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

    def test_unexisting_top_thumbnail(self):
        from calibrationreport.views import ThumbnailViews
        # Request the top of the pdf thumbnail, expect a placeholder png
        # if that device does not exist on disk

        # Get size of actual file on disk, compare
        file_name = "database/imagery/top_placeholder.png"
        actual_size = os.path.getsize(file_name)

        request = testing.DummyRequest()
        request.matchdict["serial"] = "BADDevice123"
        inst = ThumbnailViews(request)
        view_back = inst.top_thumbnail()

        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")
        
        # Specify a known existing file with a relative pathname, verify
        # it is unavailable by expecting the file size of the
        # placeholder image
        file_name = "database/imagery/../_empty_directory_required_"
        request.matchdict["serial"] = file_name 
        inst = ThumbnailViews(request)
        view_back = inst.top_thumbnail()
        
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

    def test_existing_top_thumbnail(self):
        from calibrationreport.views import ThumbnailViews
        # Add a known file into the imagery folder
        serial = "test0123" # slug-friendly serial
        dir_name = "database/imagery/%s" % serial
        dest_file = "%s/top_thumbnail.png" % dir_name
        src_file = "database/imagery/known_top_image.png"

        result = os.makedirs(dir_name)
        result = shutil.copy(src_file, dest_file) 

        # Verify that it can be viewed
        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = ThumbnailViews(request)
        view_back = inst.top_thumbnail()

        actual_size = os.path.getsize(src_file)
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

    def test_unexisting_mosaic_thumbnail(self):
        from calibrationreport.views import ThumbnailViews
        # Request the mosaic thumbnail of the pdf, expect a placeholder
        # png if that device does not exist on disk

        # Get size of actual file on disk, compare
        file_name = "database/imagery/mosaic_placeholder.png"
        actual_size = os.path.getsize(file_name)

        request = testing.DummyRequest()
        request.matchdict["serial"] = "BADDevice111"
        inst = ThumbnailViews(request)
        view_back = inst.mosaic_thumbnail()

        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

        # Specify a known existing file with a relative pathname, verify
        # it is unavailable by expecting the file size of the
        # placeholder image
        file_name = "database/imagery/../_empty_directory_required_"
        request.matchdict["serial"] = file_name 
        inst = ThumbnailViews(request)
        view_back = inst.mosaic_thumbnail()
        
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")

    def test_existing_mosaic_thumbnail(self):
        from calibrationreport.views import ThumbnailViews
        # Add a known file into the imagery folder
        serial = "test0123" # slug-friendly serial
        dir_name = "database/imagery/%s" % serial
        dest_file = "%s/mosaic_thumbnail.png" % dir_name
        src_file = "database/imagery/known_mosaic_image.png"

        result = os.makedirs(dir_name)
        result = shutil.copy(src_file, dest_file) 

        # Verify that it can be viewed
        request = testing.DummyRequest()
        request.matchdict["serial"] = serial
        inst = ThumbnailViews(request)
        view_back = inst.mosaic_thumbnail()

        actual_size = os.path.getsize(src_file)
        self.assertEqual(view_back.content_length, actual_size)
        self.assertEqual(view_back.content_type, "image/png")


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from calibrationreport import main
        settings = {}
        app = main({}, **settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        del self.testapp

    def test_root(self):
        res = self.testapp.get("/")
        #log.info("Root res: %s", res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue("calibrationreport" in res.body)

    def test_top_level_image(self):

        url = "/top_thumbnail"

        # known unknown serial is placeholder
        serial = "knowitsbad"
        res = self.testapp.get("%s/%s" % (url, serial))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "image/png")
        # Why are you doing this in the unit and in the functional test?
        self.assertEqual(res.content_length, 36090)

   
        # non-existent serial - why does this return an exception
        # instead of an actual 404? Because you need expect_errors:
        # https://github.com/django-webtest/django-webtest/issues/30
        res = self.testapp.get("%s" % url, expect_errors=True)
        self.assertEqual(res.status_code, 404)

    def test_mosaic_image(self):
        url = "/mosaic_thumbnail"

        # known unkonwn serial is a placeholder
        serial = "badmosaic"
        res = self.testapp.get("%s/%s" % (url, serial))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "image/png")
        self.assertEqual(res.content_length, 57037)
        
        # Expect an error on non-existent serial
        res = self.testapp.get(url, expect_errors=True)
        self.assertEqual(res.status_code, 404)
    
    def test_form_submission_shows_thumbnails(self):
        url = "/add_pdf"

        # template shows no image specified text based on serial number
        res = self.testapp.get(url)

        # Form is not populated
        form = res.forms["pdf_form"]
        self.assertEqual(form["serial"].value, "")
        self.assertEqual(form["file_content"].value, "")

        # Image links do not exist
        self.assertTrue("top_thumbnail.png" not in res)
        self.assertTrue("mosaic_thumbnail.png" not in res)

        # After succesful upload, template shows form with fields
        # pre-populated and thumbnail images
        source_file = "database/imagery/known_unittest.pdf"
        test_serial = "functest1234"
        form["serial"] = test_serial
        form["file_content"] = Upload(source_file) 

        submit_res = form.submit("form.submitted")
        self.assertEquals(submit_res.status_code, 200)

        top_link = "top_thumbnail/%s" % test_serial
        self.assertTrue(top_link in submit_res)

        mos_link = "mosaic_thumbnail/%s" % test_serial
        self.assertTrue(mos_link in submit_res)
