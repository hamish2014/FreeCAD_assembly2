if __name__ == '__main__':
    print('''run tests via
    FreeCAD_assembly2$ python2 test.py assembly2.utils.tests''')
    exit()

import unittest

class Tests_Animate_Constraint(unittest.TestCase):
    def test_interpolation(self):
        from assembly2.utils.animate_constraint import numpy, spline_interp, linear_interp
        P = [
            [ 0, 0],
            [ 1, -1],
            [ 1, -4],
            [ 0, -5],
            [ 4, -6],
            [10, -4],
            [8, -4],
            [6, -5],
            [3, -2]
        ]
        A = numpy.arange( len(P) ) * 4.2
        P_spline = spline_interp( P, A, 16 )
        P_linear = linear_interp( P, A, 16 )
        if False:
            from matplotlib import pyplot
            pyplot.figure()
            pyplot.plot( P_spline[:,0], P_spline[:,1], '-bx' )
            pyplot.plot( P_linear[:,0], P_linear[:,1], '--g' )
            pyplot.plot( [p[0] for p in P], [p[1] for p in P], 'go' )
            pyplot.show()
