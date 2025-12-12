from slapos.tests.test_slapproxy import BasicMixin
import unittest
import httpretty

class HttpProxyTestCase(BasicMixin, unittest.TestCase):

  @httpretty.activate
  def test_full_request(self):
    url_to_proxy = 'http://example.org/my/path'
    httpretty.register_uri(
        httpretty.GET,
        url_to_proxy,
        status=201,
        body="bar\nfoo\n",
        adding_headers={
            # whilelisted
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
        }
    )
    response = self.app.get(
        '/http_proxy/http/example.org/my/path',
        query_string={
          "key1": "value1",
          "key2": "value2"
        },
        headers={
            # whitelisted
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

    # Response status code
    assert response.status_code == 201, response.status_code

    last_request = httpretty.last_request()

    # Request path and query string
    assert last_request.path in ['/my/path?key1=value1&key2=value2', '/my/path?key2=value2&key1=value1'], last_request.path

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

  @httpretty.activate
  def test_path_propagated(self):
    httpretty.register_uri(
        httpretty.GET,
        'http://example.org/a/b',
        body="http://example.org/a/b",
    )
    httpretty.register_uri(
        httpretty.GET,
        'http://example.org/a',
        body="http://example.org/a",
    )
    httpretty.register_uri(
        httpretty.GET,
        'http://example.org/',
        body="http://example.org/",
    )
    httpretty.register_uri(
        httpretty.GET,
        'http://example.org',
        body="http://example.org",
    )

    response = self.app.get('/http_proxy/http/example.org')
    assert response.status_code == 200, response.status_code
    last_request = httpretty.last_request()
    assert last_request.path == '/', last_request.path
    assert response.data == b'http://example.org', response.data

    response = self.app.get('/http_proxy/http/example.org/')
    assert response.status_code == 200, response.status_code
    last_request = httpretty.last_request()
    assert last_request.path == '/', last_request.path
    assert response.data == b'http://example.org/', response.data

    response = self.app.get('/http_proxy/http/example.org/a')
    assert response.status_code == 200, response.status_code
    last_request = httpretty.last_request()
    assert last_request.path == '/a', last_request.path
    assert response.data == b'http://example.org/a', response.data

    response = self.app.get('/http_proxy/http/example.org/a/b')
    assert response.status_code == 200, response.status_code
    last_request = httpretty.last_request()
    assert last_request.path == '/a/b', last_request.path
    assert response.data == b'http://example.org/a/b', response.data
