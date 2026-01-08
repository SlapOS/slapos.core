from slapos.tests.test_slapproxy import BasicMixin
import os
import unittest
import tempfile
import shutil


class TemporaryDirectory(object):
    """
    Context manager for tempfile.mkdtemp().
    This class is available in python +v3.2.
    """
    def __enter__(self):
        self.dir_name = tempfile.mkdtemp()
        return self.dir_name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.dir_name)

TemporaryDirectory = getattr(tempfile, 'TemporaryDirectory',
                             TemporaryDirectory)


class PanelTestCase(BasicMixin, unittest.TestCase):

  def test_index_page(self):
    response = self.app.get('/panel/')

    # Response status code
    assert response.status_code == 200, response.status_code

    # Response body
    assert b'<script src="panel.js">' in response.data, response.data
    assert b'<script src="external/renderjs.js">' in response.data, response.data

    # Response header forced
    assert response.headers["Content-Type"] == \
        "text/html; charset=utf-8", \
        response.headers
    assert response.headers["Content-Length"] == \
        "3105", \
        response.headers

  def test_panel_dependencies(self):
    response = self.app.get('/panel/panel.js')

    # Response status code
    assert response.status_code == 200, response.status_code

    # Response body
    assert b'callJsonRpcEntryPoint' in response.data, response.data

    # Response header forced
    assert response.headers["Content-Type"] in \
        ["application/javascript; charset=utf-8", \
         "text/javascript; charset=utf-8"], \
        response.headers
    assert response.headers["Content-Length"] == \
        "32035", \
        response.headers

  def test_panel_external_dependencies(self):
    response = self.app.get('/panel/external/renderjs.js')

    # Response status code
    assert response.status_code == 200, response.status_code

    # Response body
    assert b'clearGadgetInternalParameters' in response.data, response.data

    # Response header forced
    assert response.headers["Content-Type"] in \
        ["application/javascript; charset=utf-8", \
         "text/javascript; charset=utf-8"], \
        response.headers
    assert response.headers["Content-Length"] == \
        "107174", \
        response.headers

  def test_panel_public_directory_not_configured(self):
    response = self.app.get('/panel/public/foo')
    assert response.status_code == 403, response.status_code
    assert b'The public directory path is not configured.' in response.data, response.data

  def test_panel_public_directory_configured(self):
    with TemporaryDirectory() as tmpdirname:
      with tempfile.NamedTemporaryFile(dir=tmpdirname) as fp:
        fp.write(b'Hello world!')
        fp.seek(0)
        base_name = os.path.basename(fp.name)
        self.app_config['PUBLIC_DIRECTORY_PATH'] = tmpdirname
        response = self.app.get('/panel/public/' + base_name)
    self.app_config.pop('PUBLIC_DIRECTORY_PATH')
    assert response.status_code == 200, response.status_code
    assert b'Hello world!' == response.data, response.data
    assert response.headers["Content-Disposition"] == "attachment; filename=%s" % base_name, response.headers
