import unittest
import sys, os
sys.path.append('/usr/lib/freecad/lib/') #path to FreeCAD library on Linux
try:
    import FreeCAD, FreeCADGui
except ImportError as msg:
    print('Import error, is this testing script being run from Python2?')
    raise ImportError(msg)
assert not hasattr(FreeCADGui, 'addCommand')

def addCommand_check( name, command):
    pass
    #if not name.startswith('assembly2_'):
    #    raise ValueError('%s does not begin with %s' % ( name, 'assembly2_' ) )

FreeCADGui.addCommand = addCommand_check

import assembly2
import argparse
from assembly2.core import debugPrint

parser = argparse.ArgumentParser()
parser.add_argument('--failfast', action='store_true', help='Stop the test run on the first error or failure.')
parser.add_argument('--buffer', action='store_true', help='The standard output and standard error streams are buffered during the test run. Output during a passing test is discarded. Output is echoed normally on test fail or error and is added to the failure messages.')
parser.add_argument('-v','--verbosity', type=int, default=1 )
parser.add_argument('--no_descriptions', action='store_true' )
parser.add_argument('testSuiteName',  type=str, nargs='*')
args = parser.parse_args()

debugPrint.level = 0

testLoader = unittest.TestLoader()
if args.testSuiteName == []:
    suite = testLoader.discover(
        start_dir = os.path.join( assembly2.__dir__ , 'assembly2' ),
        pattern='test*.py',
        top_level_dir=None
    )
else:
    suite = unittest.TestSuite()
    for name in args.testSuiteName:
        suite.addTest( testLoader.loadTestsFromName(name ) )

runner = unittest.TextTestRunner(
    failfast = args.failfast,
    verbosity = args.verbosity,
    descriptions = not args.no_descriptions,
    buffer = args.buffer
)
runner.run( suite )
