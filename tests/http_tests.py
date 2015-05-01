# -*- coding: utf-8 -*-
"""HTTP tests."""
import codecs
import os
import sys

import anyhttp

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    import testtools
    from testscenarios import with_scenarios
except ImportError:
    raise unittest.SkipTest("""
testscenarios.with_scenarios not found.
Please fetch and install testscenarios from:
https://code.launchpad.net/~jayvdb/testscenarios/0.4-with_scenarios
""")


if sys.version_info[0] > 2:
    basestring = (str, )
    unicode = str

no_redirect_support = set([
    'pycurl', 'fido', 'httq', 'async_http', 'webob', 'urlfetch', 'simplefetch',
    'httputils', 'tinydav', 'hyper', 'geventhttpclient', 'dugong',
    'yieldfrom.http.client',
])

# These two cause the following exception if run as scenario:
# NotImplementedError: gevent is only usable from a single thread
threading_problems = ['fido', 'asynchttp', 'httxlib']

anyhttp.verbose = False


class TestBase(testtools.TestCase):

    """Base test case for testing various HTTP client implementation."""

    def setUp(self):
        """Set up anyhttp."""
        anyhttp.http = None
        anyhttp.loaded_http_packages = None
        super(TestBase, self).setUp()

    @property
    def request_url(self):
        raise RuntimeError('abstract property')

    def check_response(self, value):
        raise RuntimeError('abstract method')

    def _load_package(self):
        name = self.package  # load name from scenario

        if name in threading_problems and 'FORCE_TEST' not in os.environ:
            self.skipTest('%s causes threading problems' % name)

        if name in anyhttp.unsupported_http_packages:
            self.skipTest('%s is not supported on this platform' % name)

        try:
            __import__(name)
        except ImportError as e:
            self.skipTest('%s could not be imported: %r' % (name, e))

        assert(name in sys.modules)

        anyhttp.detect_loaded_package()
        assert(name in anyhttp.package_handlers.keys())
        self.assertIn(name, anyhttp.loaded_http_packages)

    def select_package(self):
        name = self.package  # load name from scenario
        self._load_package()
        anyhttp.loaded_http_packages = set([name])

    def do_get_text(self):
        self.select_package()

        result = anyhttp.get_text(self.request_url)

        self.assertIsNotNone(result)

        self.assertIsInstance(result, basestring)

        self.check_response(result)

    def do_get_bin(self):
        self.select_package()

        result = anyhttp.get_binary(self.request_url)

        self.assertIsNotNone(result)

        self.assertIsInstance(result, bytes)

        self.check_response(result)


class TestAll(TestBase):

    """Set scenarios to include all clients."""

    expected_file = None

    scenarios = [(name.replace('.', '_'), {'package': name})
                 for name in anyhttp.package_handlers.keys()]


@with_scenarios()
class TestGetText(TestAll):

    """Test all clients for text requests."""

    expected_file = 'utf8.txt'

    @classmethod
    def setUpClass(cls):
        with codecs.open(os.path.join(os.path.split(__file__)[0],
                                      cls.expected_file),
                         'r', 'utf8') as f:
            cls.expected_value = f.read()

    @property
    def request_url(self):
        return 'http://httpbin.org/encoding/utf8'

    test = TestBase.do_get_text

    def check_response(self, value):
        # assertEqual will dump out lots of unreadable information
        self.assertEqual(value, self.expected_value)


@with_scenarios()
class TestGetBin(TestAll):

    """Test all clients for binary requests."""

    expected_file = 'pig.png'

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(os.path.split(__file__)[0],
                               cls.expected_file),
                  'rb') as f:
            cls.expected_value = f.read()

    @property
    def request_url(self):
        return 'http://httpbin.org/image/png'

    test = TestBase.do_get_bin

    def check_response(self, value):
        # assertEqual will dump out lots of unreadable information
        self.assertEqual(value, self.expected_value)


@with_scenarios()
class TestRedirects(TestAll):

    """Test all clients for absolute redirects."""

    @property
    def request_url(self):
        return 'http://httpbin.org/absolute-redirect/2'

    def check_response(self, value):
        if self.package in no_redirect_support:
            # remove the '2' from the end of the url and add '1'
            self.assertTrue(self.request_url[:-1] + '1' in value)
        else:
            self.assertTrue('http://httpbin.org/get' in value)
            self.assertFalse('If not click the link' in value)

    test = TestBase.do_get_text


@with_scenarios()
class TestRelativeRedirects(TestAll):

    """Test all clients for relative redirects."""

    @property
    def request_url(self):
        return 'http://httpbin.org/relative-redirect/2'

    def check_response(self, value):
        if self.package in no_redirect_support:
            self.assertEqual('', value)
        else:
            self.assertTrue('http://httpbin.org/get' in value)
            self.assertFalse('If not click the link' in value)

    test = TestBase.do_get_text

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
