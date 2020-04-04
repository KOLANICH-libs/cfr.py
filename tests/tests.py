#!/usr/bin/env python3
import sys
from pathlib import Path
import unittest

thisDir = Path(__file__).absolute().parent
parentDir = thisDir.parent

sys.path.insert(0, str(parentDir))

from collections import OrderedDict

dict = OrderedDict

from cfr import Decompilation, CFRClassPath, cfrReaderNs

class Tests(unittest.TestCase):
	def testCompile(self):
		d = Decompilation()
		d.appendClassPath(CFRClassPath)
		c = d.loadClass(cfrReaderNs + ".CfrDriverImpl")
		m = c.analyseMethod("analyse")
		print(m.decompile())


if __name__ == "__main__":
	unittest.main()
