import unittest
import sys, numpy
sys.path.append('/usr/lib/freecad/lib/') #path to FreeCAD library
try:
    import FreeCAD, FreeCADGui
except ImportError as msg:
    print('Import error, is this testing script being run from Python2?')
    raise ImportError(msg)
FreeCADGui.addCommand = lambda x,y:0
FreeCAD.headless = True
from FreeCAD import Base
import Part
import os
from fcstd_parser import Fcstd_File_Parser

class Test_Fcstd_Parser(unittest.TestCase):

    def test_clr_parser( self ):
        from fcstd_parser import parse_App_PropertyColor
        v = parse_App_PropertyColor( 0b11001000110010001100100000000 )
        error = numpy.linalg.norm( numpy.array(v) - numpy.array( [0.09803921729326248, 0.09803921729326248, 0.09803921729326248, 0.0] ) )
        self.assertTrue(
            error < 10**-8, "%s != %s" % (v, (0.09803921729326248, 0.09803921729326248, 0.09803921729326248, 0.0))
        )

    def _test_parsing( self, Doc, fn ):
        from fcstd_parser import Fcstd_File_Parser
        assert not os.path.exists( fn ), "%s exists" % fn
        Doc.saveAs( fn )
        try:
            d = Fcstd_File_Parser( fn )
        finally:
            os.remove(fn)
        return d
            
        
    def test_simple_box( self ):
        Doc = FreeCAD.newDocument('doc1')
        Doc.addObject("Part::Box","Box")
        Doc.Box.Placement.Base = Base.Vector( 2, 3, 4 )
        Doc.recompute()
        d = self._test_parsing( Doc, '/tmp/test_a2import_block.fcstd' )
        self.assertTrue( d.Name == 'test_a2import_block', d.Name )

    def est_all( self ):
        for root, dirs, files in os.walk('/home/'):
            for f in files:
                if f.endswith('.fcstd'):
                    fn = os.path.join( root, f )
                    print(fn)
                    Fcstd_File_Parser( fn )
        
    #def test_more_complicated_part( self ):
    #    f2 = Fcstd_File_Parser( '/tmp/part2.fcstd' )
    #    self.assertTrue( f2.Name == 'part2', f2.Name )

    def est_load_assembly( self ):
        Fcstd_File_Parser( '/tmp/assem1.fcstd', printLevel=0 )
        

class Test_Paths(unittest.TestCase):

    def test_splitting_and_rejoining( self ):
        from importPath import ntpath, posixpath, path_split, path_join
        def sub( pathLib, path ):
            parts = path_split( pathLib, path )
            path2 = path_join(pathLib, parts )
            self.assertTrue(
                path == path2,
                '"%s" != "%s"' % ( path, path2 )
            )
        #sub( ntpath, 'C:/Users/gyb/Desktop/Circular Saw Jig\Side support V1.00.FCStd') #known fails
        #sub( ntpath, 'C:/Users/gyb/Desktop/Circular Saw Jig/Side support V1.00.FCStd') #known fails
        sub( posixpath, '/temp/hello1/foo.FCStd')

    def test_conversion( self ):
        from importPath import ntpath, posixpath, path_convert
        path = r'C:\Users\gyb\Desktop\Circular Saw Jig\Side support V1.00.FCStd'
        converted = path_convert( path, ntpath, posixpath)
        correct = 'C:/Users/gyb/Desktop/Circular Saw Jig/Side support V1.00.FCStd'
        self.assertEqual( converted, correct )
        
if __name__ == '__main__':
    unittest.main()
