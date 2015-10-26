""" datamodel objects used by the calibrationreport project.
"""
import colander
from deform import widget, FileData

class EmptyReport(object):
    """ Helper class for empty calibration report population.
    """
    serial = ""
    filename = ""
    coefficient_0 = ""
    coefficient_1 = ""
    coefficient_2 = ""
    coefficient_3 = ""
    top_image_filename = ""
    bottom_image_filename = ""

class MemoryTmpStore(dict):
    """ Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface
    This is from the deform2demo code: 
    https://github.com/Pylons/deformdemo/blob/master/deformdemo/\
        __init__.py
    If you attempt to make tmpstore a class of FileUploadTempStore as
    described in the stack overflow entry below, it complains about
    the missing implementation of preview_url.
    """
    def preview_url(self, uid):
        """ provide interface for schemanode
        """
        return None


class ReportSchema(colander.Schema):
    """ use colander to define a data validation schema for linkage with
    a deform object.
    """
    csn = colander.SchemaNode

    serial = csn(colander.String(),
                 validator=colander.Length(3, 10))

    coefficient_0 = csn(colander.String())

    coefficient_1 = csn(colander.String())

    coefficient_2 = csn(colander.String())

    coefficient_3 = csn(colander.String())

    # Based on: # http://stackoverflow.com/questions/6563546/\
    # how-to-make-file-upload-facultative-with-deform-and-colander
    # Various demos delete this temporary file on succesful submission
    top_tmp_store = MemoryTmpStore()
    fuw = widget.FileUploadWidget(top_tmp_store)
    top_image_upload = csn(FileData(), 
                           missing=colander.null,
                           widget=fuw)

    bottom_tmp_store = MemoryTmpStore()
    fuw = widget.FileUploadWidget(bottom_tmp_store)
    bottom_image_upload = csn(FileData(), 
                              missing=colander.null,
                              widget=fuw)
