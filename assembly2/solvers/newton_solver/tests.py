if __name__ == '__main__':
    print('''run tests via
  FreeCAD_assembly2$ python2 test.py assembly2.solvers.newton_solver.tests.Test_Newton_Slsqp_Solver''')
    exit()

import unittest
import FreeCAD
import assembly2
import os, time, numpy
test_assembly_path = os.path.join( assembly2.__dir__ , 'assembly2', 'solvers', 'test_assemblies' )
from assembly2.solvers import solveConstraints
from assembly2.core import debugPrint


class Stats:
    pass
stats = Stats()

# To do
#   from assembly2.solvers.dof_reduction_solver.tests import Test_Dof_Reduction_Solver
#   class Test_Newton_Slsqp_Solver(Test_Dof_Reduction_Solver):
#
#   proper solution checking to be implemented
#
class Test_Newton_Slsqp_Solver(unittest.TestCase):

    use_cache = False

    @classmethod
    def setUpClass(cls):
        stats.t_solver = 0
        stats.t_cache = 0
        stats.t_start = time.time()
        stats.n_attempted = 0
        stats.n_solved = 0
        

    @classmethod
    def tearDownClass(cls):
        debugPrint(0,'\n------------------------------------------')
        debugPrint(0,'  Newton_slsqp_solver passed %i/%i tests' % ( stats.n_solved, stats.n_attempted ) )
        debugPrint(0,'    time solver:            %3.2f s' % stats.t_solver )
        debugPrint(0,'    time cached solutions:  %3.2f s' % stats.t_cache )
        debugPrint(0,'    total running time:     %3.2f s' % (time.time() - stats.t_start) )
        debugPrint(0,'------------------------------------------')

    
    def _test_file( self, testFile_basename, solution = None ):
        testFile = os.path.join( test_assembly_path, testFile_basename + '.fcstd' )
        debugPrint(1, testFile_basename )
        stats.n_attempted += 1
        #if testFile == 'tests/testAssembly11-Pipe_assembly.fcstd':
        #    print('Skipping known fail')
        #    continue
        doc =  FreeCAD.open(testFile)
        t_start_solver = time.time()
        xOpt = solveConstraints( doc, solver_name = 'newton_solver_slsqp', use_cache = self.use_cache, showFailureErrorDialog=False )
        if solution:
            self.check_solution( xOpt, solution )
        stats.t_solver += time.time() - t_start_solver
        assert not self.use_cache
        if not xOpt is None:
            stats.n_solved += 1
        FreeCAD.closeDocument( doc.Name )
        debugPrint(1,'\n\n\n')
        return xOpt
        
    def testAssembly_01_2_cubes( self ):
        X = self._test_file( 'testAssembly_01' )

    def testAssembly_02_3_cubes( self ):
        self._test_file( 'testAssembly_02' )

    def testAssembly_03_2_cubes( self ):
        self._test_file( 'testAssembly_03' ) 

    def testAssembly_04_angle_constraint( self ):
        x_c = self._test_file( 'testAssembly_04')
        self.assertFalse( x_c is None )
        a = x_c[0:3]
        b = numpy.array(  [-14.7637558, -1.81650472,  16.39465332] )
        self.assertTrue(
            len(a) == len(b) and  numpy.allclose( a, b ),
            'Solver solution incorrect: %s != %s' % ( a, b )
        )

    @unittest.skip("takes along time to run")      
    def testAssembly_05( self ):
        self._test_file( 'testAssembly_05')

    @unittest.skip("takes along time to run")          
    def testAssembly_06( self ):
        self._test_file( 'testAssembly_06')

    @unittest.skip("takes along time to run")      
    def testAssembly_07( self ):
        self._test_file( 'testAssembly_07')

    @unittest.skip("known fail which takes along time to run")    
    def testAssembly_08( self ):
        self._test_file( 'testAssembly_08')

    @unittest.skip("takes along time to run")      
    def testAssembly_09( self ):
        self._test_file( 'testAssembly_09')

    @unittest.skip("error: failed in converting 4th argument `xl' of _slsqp.slsqp to C/Fortran array")
    def testAssembly_10_block_iregular_constraint_order( self ):
        self._test_file( 'testAssembly_10-block_iregular_constraint_order')

    @unittest.skip("known failuire with lots of output")
    def testAssembly_11_pipe_assembly( self ):
        self._test_file( 'testAssembly_11-pipe_assembly')

    @unittest.skip("takes along time to run")      
    def testAssembly_11b_pipe_assembly( self ):
        self._test_file( 'testAssembly_11b-pipe_assembly')

    #@unittest.skip("takes along time to run")       
    def testAssembly_12_angles_clock_face( self ):
        self._test_file( 'testAssembly_12-angles_clock_face')
    #@unittest.skip("takes along time to run")     
    def testAssembly_13_spherical_surfaces_hip( self ):
        self._test_file( 'testAssembly_13-spherical_surfaces_hip')
    #@unittest.skip
    def testAssembly_13_spherical_surfaces_cube_vertices( self ):
        self._test_file( 'testAssembly_13-spherical_surfaces_cube_vertices')

    @unittest.skip("error: failed in converting 4th argument `xl' of _slsqp.slsqp to C/Fortran array")
    def testAssembly_14_lock_relative_axial_rotation( self ):
        self._test_file( 'testAssembly_14-lock_relative_axial_rotation')

    #@unittest.skip("takes along time to run")     
    def testAssembly_15_triangular_link_assembly( self ):
        self._test_file( 'testAssembly_15-triangular_link_assembly')

    @unittest.skip("takes along time to run")     
    def testAssembly_16_revolved_surface_objs( self ):
        self._test_file( 'testAssembly_16-revolved_surface_objs')

    #@unittest.expectedFailure
    @unittest.skip("to do")
    def testAssembly_17_bspline_objects( self ):
        self._test_file( 'testAssembly_17-bspline_objects')

    @unittest.skip("takes along time to run")     
    def testAssembly_18_add_free_objects( self ):
        self._test_file( 'testAssembly_18-add_free_objects')
