from __future__ import unicode_literals

import pdfkit, os, frappe
from frappe.utils import scrub_urls
from frappe import _
from PyPDF2 import PdfFileReader, PdfFileWriter
from bs4 import BeautifulSoup
import io
from distutils.version import LooseVersion

from frappe.utils.pdf import cleanup, read_options_from_html, get_wkhtmltopdf_version,  get_file_data_from_writer


def get_pdf(html, options=None, output=None):
        html = scrub_urls(html)
        html, options = prepare_options(html, options)

        options.update({
                "disable-javascript": "",
                "disable-local-file-access": ""
        })

        filedata = ''
        if LooseVersion(get_wkhtmltopdf_version()) > LooseVersion('0.12.3'):
                options.update({"disable-smart-shrinking": ""})

        try:
                # Set filename property to false, so no file is actually created
                filedata = pdfkit.from_string(html, False, options=options or {})
                # https://pythonhosted.org/PyPDF2/PdfFileReader.html
                # create in-memory binary streams from filedata and create a Pdf                                                                                       FileReader object
                reader = PdfFileReader(io.BytesIO(filedata))
        except OSError as e:
                if any([error in str(e) for error in PDF_CONTENT_ERRORS]):
                        if not filedata:
                                frappe.throw(_("PDF generation failed because of broken image links"))
                        # allow pdfs with missing images if file got created
                        if output:  # output is a PdfFileWriter object
                                output.appendPagesFromReader(reader)
                else:
                        raise

        if "password" in options:
                password = options["password"]
                if six.PY2:
                        password = frappe.safe_encode(password)

        if output:
                output.appendPagesFromReader(reader)
                return output

        writer = PdfFileWriter()
        writer.appendPagesFromReader(reader)

        if "password" in options:
                writer.encrypt(password)

        filedata = get_file_data_from_writer(writer)

        return filedata

@frappe.whitelist()
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0):
	html = frappe.get_print(doctype, name, format, doc=doc, no_letterhead=no_letterhead)
	frappe.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = get_pdf(html)
	frappe.local.response.type = "download"
'''
def get_pdf(html, options=None, output = None):
	html = scrub_urls(html)
	html, options = prepare_options(html, options)
	fname = os.path.join("/tmp", "frappe-pdf-{0}.pdf".format(frappe.generate_hash()))

	try:
		pdfkit.from_string(html, fname, options=options or {})
		if output:
			append_pdf(PdfFileReader(fname),output)
		else:
			with open(fname, "rb") as fileobj:
				filedata = fileobj.read()

	except IOError as e:
		if ("ContentNotFoundError" in e.message
			or "ContentOperationNotPermittedError" in e.message
			or "UnknownContentError" in e.message
			or "RemoteHostClosedError" in e.message):

			# allow pdfs with missing images if file got created
			if os.path.exists(fname):
				with open(fname, "rb") as fileobj:
					filedata = fileobj.read()

			else:
				frappe.throw(_("PDF generation failed because of broken image links"))
		else:
			raise

	finally:
		cleanup(fname, options)

	if output:
		return output

	return filedata

'''

def prepare_options(html, options):
	if not options:
		options = {}

	options.update({
		'print-media-type': None,
		'background': None,
		'images': None,
		'quiet': None,
		# 'no-outline': None,
		'encoding': "UTF-8",
		#'load-error-handling': 'ignore',

		# defaults
		'margin-right': '2mm',
		'margin-left': '2mm'
	})

	html, html_options = read_options_from_html(html)
	options.update(html_options or {})

	# cookies
	if frappe.session and frappe.session.sid:
		options['cookie'] = [('sid', '{0}'.format(frappe.session.sid))]

	# page size
	if not options.get("page-size"):
		options['page-size'] = frappe.db.get_single_value("Print Settings", "pdf_page_size") or "A4"

	return html, options
