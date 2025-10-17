from test_slapproxy import BasicMixin
import os
import unittest
import tempfile

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
    assert response.headers["Content-Type"] == \
        "application/javascript; charset=utf-8", \
        response.headers
    assert response.headers["Content-Length"] == \
        "22736", \
        response.headers

  def test_panel_external_dependencies(self):
    response = self.app.get('/panel/external/renderjs.js')

    # Response status code
    assert response.status_code == 200, response.status_code

    # Response body
    assert b'clearGadgetInternalParameters' in response.data, response.data

    # Response header forced
    assert response.headers["Content-Type"] == \
        "application/javascript; charset=utf-8", \
        response.headers
    assert response.headers["Content-Length"] == \
        "107174", \
        response.headers
