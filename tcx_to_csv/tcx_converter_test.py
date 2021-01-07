import unittest
import sys
from argparse import ArgumentParser
import base64
from io import StringIO
from tcx_converter import convert_to_csv

import pandas as pd

class ConvertBytestrTest(unittest.TestCase):
    def test_tcx_conversion_from_string(self):
        with open('../cypress/fixtures/test_cycling_data.tcx', 'r') as test_f:
            tcxStr = test_f.read()
            tcx_bytestring = bytes(bytearray(tcxStr, encoding = 'utf-8'))
            csvTup = convert_to_csv(tcx_bytestring, src_type='string')
            self.assertIsInstance(csvTup, tuple)
            for tup in csvTup:
                filename, csvStr = tup
                df = pd.read_csv(StringIO(csvStr) , comment='#')
                df.to_csv('./example.csv', index=False)

if __name__ == '__main__':
    unittest.main()
