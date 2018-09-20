if __name__ == '__main__':
    print('''run tests via
  FreeCAD_assembly2$ python2 test.py assembly2.solvers.dof_reduction_solver.tests''')
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

class Test_Dof_Reduction_Solver(unittest.TestCase):
    use_cache = True

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
        debugPrint(0,'  dof_reduction_solver passed %i/%i tests' % ( stats.n_solved, stats.n_attempted ) )
        debugPrint(0,'    time solver:            %3.2f s' % stats.t_solver )
        debugPrint(0,'    time cached solutions:  %3.2f s' % stats.t_cache )
        debugPrint(0,'    total running time:     %3.2f s' % (time.time() - stats.t_start) )
        debugPrint(0,'------------------------------------------')


    def get_solver_X( self, solver_result ):
        return solver_result.variableManager.X
        
    def check_solution( self, solver_result, solution ):
        a = self.get_solver_X( solver_result )
        b = solution if type( solution ) != str else [ float(v) for v in solution[1:-1].split() ]
        self.assertTrue(
            len(a) == len(b) and  numpy.allclose( a, b ),
            'Solver solution incorrect: %s != %s' % ( a, b )
        )
        
        
    def _test_file( self, testFile_basename, solution = None ):
        testFile = os.path.join( test_assembly_path, testFile_basename + '.fcstd' )
        debugPrint(1, testFile_basename )
        stats.n_attempted += 1
        #if testFile == 'tests/testAssembly11-Pipe_assembly.fcstd':
        #    print('Skipping known fail')
        #    continue
        doc =  FreeCAD.open(testFile)
        t_start_solver = time.time()
        constraintSystem = solveConstraints( doc, solver_name = 'dof_reduction_solver', use_cache = self.use_cache, showFailureErrorDialog=False )
        if solution:
            self.check_solution( constraintSystem, solution )
        stats.t_solver += time.time() - t_start_solver
        if  self.use_cache:
            debugPrint(1,'\n\n')
            X_org = constraintSystem.variableManager.X
            t_start_cache = time.time()
            #cache.debugMode = 1
            constraintSystem = solveConstraints( doc, solver_name = 'dof_reduction_solver', use_cache =  self.use_cache )
            self.assertTrue(
                numpy.allclose( X_org , constraintSystem.variableManager.X ),
                'Cache solution differs from originial solution: %s != %s' % ( X_org , constraintSystem.variableManager.X )
            )
            #cache.debugMode = 0
            stats.t_cache += time.time() - t_start_cache
            constraintSystem.update()
        stats.n_solved += 1
        FreeCAD.closeDocument( doc.Name )
        debugPrint(1,'\n\n\n')
        
    def testAssembly_01_2_cubes( self ):
        X = self._test_file( 'testAssembly_01', [ 0 ]*6 + [ 3,  2,  2, -2.35619449, 0.61547971,  2.0943951 ] )

    def testAssembly_02_3_cubes( self ):
        self._test_file( 'testAssembly_02', '[-14.57140808  22.69204404   0.72612381  -2.0943951    1.57079633  -2.0943951   -2.2509       4.03179      8.09739      0.           1.57079633    1.04719755  -9.57140808  31.35229808  15.70503235  -3.14159265    1.57079633   2.61799388]' )

    def testAssembly_03_2_cubes( self ):
        self._test_file( 'testAssembly_03', '[ 2.         -0.212375   -5.54064    -1.57079633  1.1559176   0.          0.  0.          0.          0.          0.          0.        ]')

    def testAssembly_04_angle_constraint( self ):
        self._test_file( 'testAssembly_04', '[-14.7637558   -1.81650472  16.39465332  -0.78539816   0.           1.57079633   0.           0.           0.           0.           0.           0.        ]')
        
    def testAssembly_05( self ):
        self._test_file( 'testAssembly_05')

    def testAssembly_06( self ):
        self._test_file( 'testAssembly_06')

    def testAssembly_07( self ):
        self._test_file( 'testAssembly_07')

    def testAssembly_08( self ):
        self._test_file( 'testAssembly_08')

    def testAssembly_09( self ):
        self._test_file( 'testAssembly_09')

    def testAssembly_10_block_iregular_constraint_order( self ):
        self._test_file( 'testAssembly_10-block_iregular_constraint_order')

    @unittest.skip("known failuire with lots of output")
    def testAssembly_11_pipe_assembly( self ):
        self._test_file( 'testAssembly_11-pipe_assembly')

    def testAssembly_11b_pipe_assembly( self ):
        self._test_file( 'testAssembly_11b-pipe_assembly')

    def testAssembly_12_angles_clock_face( self ):
        self._test_file( 'testAssembly_12-angles_clock_face')

    def testAssembly_13_spherical_surfaces_hip( self ):
        self._test_file( 'testAssembly_13-spherical_surfaces_hip')

    def testAssembly_13_spherical_surfaces_cube_vertices( self ):
        self._test_file( 'testAssembly_13-spherical_surfaces_cube_vertices')

    def testAssembly_14_lock_relative_axial_rotation( self ):
        self._test_file( 'testAssembly_14-lock_relative_axial_rotation')

    def testAssembly_15_triangular_link_assembly( self ):
        self._test_file( 'testAssembly_15-triangular_link_assembly')

    def testAssembly_16_revolved_surface_objs( self ):
        self._test_file( 'testAssembly_16-revolved_surface_objs')

    @unittest.expectedFailure
    def testAssembly_17_bspline_objects( self ):
        self._test_file( 'testAssembly_17-bspline_objects')

    def testAssembly_18_add_free_objects( self ):
        self._test_file( 'testAssembly_18-add_free_objects')




        

# python2 test.py assembly2.solvers.dof_reduction_solver.tests.Tests_solverLib
class Tests_solverLib(unittest.TestCase):

    def assertClose( self, a, b, tol= 10.0**-9 ):
        assert type(a) == float or type(a) == int or type(a) == numpy.float64, type(a)
        assert type(b) == float or type(b) == int or type(b) == numpy.float64, type(b)
        self.assertTrue(
            abs(a-b) < tol,
            'abs(a-b) > %1.1f ( a=%s, b=%s, diff=%e)' % ( tol, a, b, a-b ) 
        )
    
    def assertAllClose( self, a, b):
        self.assertTrue(
            len(a) == len(b) and  numpy.allclose( a, b ),
            'a != b: %s != %s' % ( a, b )
        )

    def f1(self,x) :
        return numpy.array([
            x[0] + x[1] -1,
            x[0]**2 - x[1] - 5
        ])
    def grad_f1(self, x):
        return numpy.array([
            [1, 1],
            [2*x[0], -1]
        ])
    
    def test_solve_via_Newtons_method( self ):
        from solverLib import solve_via_Newtons_method, rand
        maxStep = [0.5, 0.5]
        xMin = solve_via_Newtons_method( self.f1, rand(2)+3, maxStep, x_tol=0, debugPrintLevel=0 )
        self.assertAllClose( xMin, [2, -1 ] )

    def f2( self,X) :
        y,z=X
        return y + y*z + (1.0-y)**3
    
    def grad_f2(self, X):
        y,z=X
        return  numpy.array([ 1 + z - 3*(1.0-y)**2, y ])
        
    def test_gradient_approx_1( self ):
        'test on a function which returns a single value'
        from solverLib import GradientApproximatorRandomPoints, GradientApproximatorForwardDifference, GradientApproximatorCentralDifference, rand
        grad_f_rp = GradientApproximatorRandomPoints(self.f2)
        grad_f_fd = GradientApproximatorForwardDifference(self.f2)
        grad_f_cd = GradientApproximatorCentralDifference(self.f2)
        for i in range(2):
            X = rand(2)*10-5
            #print('    X %s' % X)
            #print('    grad_f(X) analytical:   %s' % grad_f2(X))
            #print('    grad_f(X) randomPoints: %s' % grad_f_rp(X))
            #print('    grad_f(X) forwardDiff.: %s' % grad_f_fd(X))
            #print('    grad_f(X) centralDiff.: %s' % grad_f_cd(X))
            #print('  norm(analytical-randomPoints) %e' % norm(grad_f2(X) - grad_f_rp(X)) )
            self.assertAllClose( self.grad_f2(X),  grad_f_rp(X) )
            self.assertAllClose( self.grad_f2(X),  grad_f_fd(X) )
            self.assertAllClose( self.grad_f2(X),  grad_f_cd(X) )
            
    def test_gradient_approx_2( self ):
        'test on a function which returns multiple values'
        from solverLib import GradientApproximatorRandomPoints, GradientApproximatorForwardDifference, GradientApproximatorCentralDifference, rand
        grad_f_rp = GradientApproximatorRandomPoints( self.f1 )
        grad_f_fd = GradientApproximatorForwardDifference( self.f1 )
        grad_f_cd = GradientApproximatorCentralDifference( self.f1 )
        for i in range(2):
            X = rand(2)*10-5
            #print('  X %s' % X)
            #print('  grad_f(X) analytical:')
            #prettyPrintArray(grad_f1(X), toStdOut, '    ','%1.6e')
            #print('  grad_f(X) randomPoints:')
            #prettyPrintArray(grad_f_rp(X), toStdOut, '    ','%1.6e')
            #print('  grad_f(X) forwardDiff:')
            #prettyPrintArray(grad_f_fd(X), toStdOut, '    ','%1.6e')
            #print('  grad_f(X) centralDiff:')
            #prettyPrintArray(grad_f_cd(X), toStdOut, '    ','%1.6e')
            #print('  error rp %e' % norm(grad_f1(X) - grad_f_rp(X)))
            self.assertAllClose( self.grad_f1(X),  grad_f_rp(X) )

    def est_plot_last_search( self ):
        import solverLib
        from solverLib import solve_via_Newtons_method, rand, SearchAnalyticsWrapper
        maxStep = [0.5, 0.5]
        xRoots = solve_via_Newtons_method( SearchAnalyticsWrapper(self.f1), rand(2)+3, maxStep, x_tol=0, debugPrintLevel=3, f_tol=10**-12)
        print( solverLib.analytics['lastSearch'] )
        solverLib.analytics['lastSearch'].plot()



# python2 test.py assembly2.solvers.dof_reduction_solver.tests.Tests_degrees_of_freedom

class Tests_degrees_of_freedom(unittest.TestCase):
    def test( self ):
        from degreesOfFreedom import PlacementDegreeOfFreedom, LinearMotionDegreeOfFreedom, AxisRotationDegreeOfFreedom, pi, normalize
        from numpy.random import rand
        from variableManager import VariableManager
        #print('creating test FreeCAD document, constraining a single Cube')
        import FreeCAD, Part
        FreeCAD.newDocument("testDoc")
        #FreeCAD.setActiveDocument("box")
        #FreeCAD.ActiveDocument = FreeCAD.getDocument("box")
        objName = "box"
        box = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", objName)
        box.Shape = Part.makeBox(2,3,2)
        #FreeCAD.ActiveDocument.recompute()
        box.Placement.Base.x = rand()
        box.Placement.Base.y = rand() + 1
        box.Placement.Base.z = rand() + 2
        #print(box.Placement)

        class FakeSystem:
            def __init__(self, variableManager):
                self.variableManager = variableManager

        vM = VariableManager(FreeCAD.ActiveDocument)
        #print(vM.X)
        constaintSystem = FakeSystem(vM)
    
        #print('\nTesting PlacementDegreeOfFreedom')
        for object_dof in range(6):
            d = PlacementDegreeOfFreedom( constaintSystem, objName, object_dof )
            #print(d)
            for i in range(6):
                value = pi*( rand() - 0.5 )
                d.setValue(value)
                assert d.getValue() == value

        #print('\nTesting LinearMotionDegreeOfFreedom')
        tol = 10**-14
        for i in range(3):
            d = LinearMotionDegreeOfFreedom( constaintSystem, objName )
            d.setDirection( normalize(rand(3) - 0.5) )
            #print(d)
            for i in range(12):
                value = 12*( rand() - 0.5 )
                d.setValue(value)
                returnedValue = d.getValue()
                if abs(returnedValue - value) > tol :
                    raise ValueError("d.getValue() - value != %1.0e, [diff %e]" % (tol, returnedValue - value))

        #print('\nTesting AxisRotationDegreeOfFreedom')
        tol = 10**-12
        for i in range(3):
            d = AxisRotationDegreeOfFreedom( constaintSystem, objName )
            axis_r =  normalize(rand(3) - 0.5) #axis in parts co-ordinate system (i.e. relative to part)
            axis = normalize(rand(3) - 0.5) # desired axis in global co-ordinate system
            d.setAxis(  axis, axis_r )
            d.setValue(0) #update azi,ela,theta to statify aligment of axis vector
            #print(d)
            for i in range(6):
                value = 2*pi*( rand() - 0.5 )
                d.setValue(value)
                returnedValue = d.getValue()
                #print('  d.getValue() %f value %f, diff %e' % (returnedValue, value, returnedValue - value))
                if abs(returnedValue - value) > tol :
                    raise ValueError("d.getValue() - value != %1.0e, [diff %e]" % (tol, returnedValue - value))
