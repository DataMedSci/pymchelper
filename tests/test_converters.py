#
#    Copyright (C) 2010-2016 pymchelper Developers.
#
#    This file is part of pymchelper.
#
#    pymchelper is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pymchelper is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pymchelper.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Tests for converters (so far only pld2sobp.py)
"""
import unittest
import logging
import pymchelper.utils.pld2sobp

logger = logging.getLogger(__name__)


class TestPld2Sobp(unittest.TestCase):
    def test_help(self):
        try:
            pymchelper.utils.pld2sobp.main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)


if __name__ == '__main__':
    unittest.main()
