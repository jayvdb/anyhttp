# -*- coding: utf-8 -*-
"""Import tests."""
import os
import sys

from .http_tests import with_scenarios, TestBase, _TestGetBase, PY3, revoked_packages

import anyhttp


@with_scenarios()
class TestSupported(TestBase):

    """Set scenarios to include all supported clients."""

    scenarios = [
        (name.replace(".", "_"), {"package": name})
        for name in anyhttp.py2_http_packages
        # Silently ignore packages that cant be tested
        if name not in revoked_packages
    ]

    def test(self):
        self.assertIn(self.package, anyhttp.package_handlers)


@with_scenarios()
class TestNotImportable(_TestGetBase, TestBase):

    """Set scenarios to include all supported clients."""

    packages = anyhttp.py2_http_packages if PY3 else []

    scenarios = [
        (name.replace(".", "_"), {"package": name})
        for name in packages
        # Silently ignore packages that cant be tested
        if name not in revoked_packages
    ]

    def test(self):
        rv = os.system("pip install {}".format(self.package))
        if rv:
            return

        rv = os.system("{} -c 'import {}'".format(sys.executable, self.package))
        if rv:
            return

        self._load_package(force=True)

        self.do_get_text()
