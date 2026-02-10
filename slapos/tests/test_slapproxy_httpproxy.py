from slapos.tests.test_slapproxy import BasicMixin
import unittest
import httmock


class HttpProxyTestCase(BasicMixin, unittest.TestCase):

  def test_full_request(self):
    captured = {}

    def handler(url, request):
      captured['url'] = url
      captured['request'] = request
      return httmock.response(
          201,
          b"bar\nfoo\n",
          headers={
              # allowed
              "Content-Type": "foo1",
              "Date": "foo2",
              "Last-Modified": "foo3",
              "Vary": "foo4",
              "Cache-Control": "foo5",
              "Etag": "foo6",
              "Accept-Ranges": "foo7",
              "Content-Range": "foo8",
              "Www-Authenticate": "foo9",
              "Access-Control-Allow-Origin": "foo10",
              "Access-Control-Allow-Methods": "foo11",
              "Access-Control-Expose-Headers": "foo12",
              "Access-Control-Allow-Headers": "foo13",
              "Access-Control-Allow-Credentials": "foo14",
              # forced
              "Content-Disposition": "foobarfoo",
              # changed
              "Location": "http://example.org/my/new/path?a=b",
              # dropped
              "Set-Cookie": "Foo",
              "foo": "bar"
          },
          request=request,
      )

    with httmock.HTTMock(handler):
      response = self.app.get(
          '/http_proxy/http/example.org/my/path',
          query_string={
            "key1": "value1",
            "key2": "value2"
          },
          headers={
              # allowed
              "Content-Type": "bar1",
              "Accept": "bar2",
              "Accept-Language": "bar3",
              "Range": "bar4",
              "If-Modified-Since": "bar5",
              "If-None-Match": "bar6",
              "User-Agent": "bar7",
              "Authorization": "bar8",
              "Origin": "bar9",
              # rejected
              "Cookie": "bar10",
              "bar11": "bar11"
          },
          data="datafoo=databar"
      )

    last_url = captured['url']
    last_request = captured['request']

    # Response status code
    assert response.status_code == 201, response.status_code

    # Request path and query string
    full_path = last_url.path
    if last_url.query:
      full_path += '?' + last_url.query
    assert full_path in ['/my/path?key1=value1&key2=value2', '/my/path?key2=value2&key1=value1'], full_path

    # Request body
    assert last_request.body == b'datafoo=databar', last_request.body

    # Request headers propagated
    assert last_request.headers['Content-Type'] == 'bar1', last_request.headers
    assert last_request.headers['Accept'] == 'bar2', last_request.headers
    assert last_request.headers['Accept-Language'] == 'bar3', last_request.headers
    assert last_request.headers['Range'] == 'bar4', last_request.headers
    assert last_request.headers['If-Modified-Since'] == 'bar5', last_request.headers
    assert last_request.headers['If-None-Match'] == 'bar6', last_request.headers
    assert last_request.headers['User-Agent'] == 'bar7', last_request.headers
    assert last_request.headers['Authorization'] == 'bar8', last_request.headers
    assert last_request.headers['Origin'] == 'bar9', last_request.headers

    # Request headers blocked
    assert 'Cookie' not in last_request.headers, last_request.headers
    assert 'bar11' not in last_request.headers, last_request.headers

    # Response body
    assert response.data == b'bar\nfoo\n', response.data

    # Response header changed
    assert response.headers["Location"] == \
        "http://localhost/http_proxy/http/example.org/my/new/path?a=b", \
        response.headers

    # Response header forced
    assert response.headers["Content-Disposition"] == \
        "attachment", \
        response.headers

    # Response headers propagated
    assert response.headers["Content-Type"] == "foo1", response.headers
    assert response.headers["Date"] == "foo2", response.headers
    assert response.headers["Last-Modified"] == "foo3", response.headers
    assert response.headers["Vary"] == "foo4", response.headers
    assert response.headers["Cache-Control"] == "foo5", response.headers
    assert response.headers["Etag"] == "foo6", response.headers
    assert response.headers["Accept-Ranges"] == "foo7", response.headers
    assert response.headers["Content-Range"] == "foo8", response.headers
    assert response.headers["Www-Authenticate"] == "foo9", response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "foo10", response.headers
    assert response.headers["Access-Control-Allow-Methods"] == "foo11", response.headers
    assert response.headers["Access-Control-Expose-Headers"] == "foo12", response.headers
    assert response.headers["Access-Control-Allow-Headers"] == "foo13", response.headers
    assert response.headers["Access-Control-Allow-Credentials"] == "foo14", response.headers

    # Response headers dropped
    assert 'Set-Cookie' not in response.headers, response.headers
    assert 'foo' not in response.headers, response.headers

  def test_path_propagated(self):
    captured = {}

    def handler(url, request):
      captured['url'] = url
      return httmock.response(200, ('http://example.org' + url.path).encode(),
                              request=request)

    with httmock.HTTMock(handler):
      response = self.app.get('/http_proxy/http/example.org')
      assert response.status_code == 200, response.status_code
      assert captured['url'].path == '/', captured['url'].path
      assert response.data == b'http://example.org/', response.data

      response = self.app.get('/http_proxy/http/example.org/')
      assert response.status_code == 200, response.status_code
      assert captured['url'].path == '/', captured['url'].path
      assert response.data == b'http://example.org/', response.data

      response = self.app.get('/http_proxy/http/example.org/a')
      assert response.status_code == 200, response.status_code
      assert captured['url'].path == '/a', captured['url'].path
      assert response.data == b'http://example.org/a', response.data

      response = self.app.get('/http_proxy/http/example.org/a/b')
      assert response.status_code == 200, response.status_code
      assert captured['url'].path == '/a/b', captured['url'].path
      assert response.data == b'http://example.org/a/b', response.data
