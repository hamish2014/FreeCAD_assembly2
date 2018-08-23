if __name__ == '__main__':
    print('''run tests via
    FreeCAD_assembly2$ python2 test.py assembly2.lib3D.tests''')
    exit()

import unittest
import numpy
from numpy import pi, sin, cos, dot
rand = numpy.random.rand
norm = numpy.linalg.norm
import sys, os 
sys.path.append( os.path.dirname( os.path.dirname(__file__) ) )

#def prettyPrintArray( A, indent='  ', fmt='%1.1e' ):
#    def pad(t):
#        return t if t[0] == '-' else ' ' + t
#    for r in A:
#        txt = '  '.join( pad(fmt % v) for v in r)
#        print(indent + '[ %s ]' % txt)    

class Test_Lib3D(unittest.TestCase):

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

    def test_quaternion_euler_angle_conversion( self ):
        from lib3D import quaternion_to_euler, euler_to_quaternion
        rotationTests = (
            #( (FreeCAD Q), (FreeCAD Q euler angles) )
            ( (0.2656567662671845, 0.25272127048434034, 0.7755360520891752, 0.5139088186548074), (109.54525270772452, -8.760320864783417, 42.29015715378342) ),
            ( (-0.26019046408365476, 0.6829999682195941, 0.19611613513818393, 0.6537204504606134), (-95.71059313749971, 84.2894068625003, -133.40658272845215) )
        )
            
        for Q, eulerAngles_FC in rotationTests:
            eulerAngles_lib3D = numpy.array( quaternion_to_euler(*Q) )/pi*180
            self.assertAllClose( eulerAngles_lib3D, eulerAngles_FC )
            ang1, ang2, ang3 = numpy.array( eulerAngles_FC )/180*pi
            self.assertAllClose( Q, euler_to_quaternion(ang1,ang2,ang3) )

    def test_rotation( self ):
        'checking that rotation using euler angles and rotation using quaterions gives the same results'
        from lib3D import  axis_rotation, quaternion, quaternion_rotation, quaternion_to_euler, euler_ZYX_rotation
        p = numpy.array([1,2,3])
        u = rand(3) - 0.5
        u = u / numpy.linalg.norm( u)
        angle = pi * 2*(rand()-0.5)
        q_1, q_2, q_3, q_0 = quaternion(angle, *u)
        ang1, ang2, ang3 = quaternion_to_euler(q_1, q_2, q_3, q_0)
        self.assertAllClose(
            axis_rotation(p, angle, *u ),
            quaternion_rotation(p, q_1, q_2, q_3, q_0 )
        )
        self.assertAllClose(
            axis_rotation(p, angle, *u ),
            euler_ZYX_rotation( p, ang1, ang2, ang3)
        )

    def generate_rotations( self, add_random_rotations=True ):
        V = []
        for r in numpy.eye(3):
            V.append( [r, 0.1 + rand() ] )
        if add_random_rotations:
            for i in range(3):
                axis = rand(3) - 0.5
                V.append( [ axis/norm(axis), 0.5-rand() ] )
        return V
        
    def test_quaternion_to_axis_and_angle( self ):
        from lib3D import quaternion, quaternion_to_axis_and_angle
        for i, axis_angle in enumerate( self.generate_rotations() ):
            axis, angle = axis_angle
            q_1, q_2, q_3, q_0  = quaternion(angle, *axis)
            axis_q, angle_q = quaternion_to_axis_and_angle(q_1, q_2, q_3, q_0)
            if numpy.sign( angle_q ) != numpy.sign( angle):
                angle_q *= -1
                axis_q *= -1
            self.assertTrue(
                norm(axis - axis_q) < 10**-12 and norm(angle - angle_q) < 10**-9,
                "norm(axis - axis_out) > 10**-12 or norm(angle - angle_out) > 10**-9. \n  in:  axis %s, angle %s\n  out: axis %s, angle %s" % (axis,angle,axis_q,angle_q)
            )

    def test_azimuth_and_elevation_angle( self ):
        from lib3D import axis_to_azimuth_and_elevation_angles, azimuth_and_elevation_angles_to_axis
        for i, axis_angle in enumerate( self.generate_rotations() ):
            axis, angle =axis_angle
            a,e = axis_to_azimuth_and_elevation_angles(*axis)
            axis_out = azimuth_and_elevation_angles_to_axis( a, e)
            self.assertTrue(
                norm(axis - axis_out) < 10**-12,
                "norm(axis - axis_out) > 10**-12. \n  in:  axis %s \n  azimuth %f, elavation %f \n  out: axis %s" % (axis,a,e,axis_out)
            )
        
    def test_distance_between_axes( self ):
        from lib3D import distance_between_axes_fmin, distance_between_axes
        p1 = numpy.array( [0.0 , 0, 0 ] )
        u1 = numpy.array( [1.0 , 0, 0 ] )
        p2 = numpy.array( [1.0, 1.0, 1.0] )
        u2 = numpy.array( [  0 , 0, 1.0 ] )
        #print('p1 %s, u1 %s, p2 %s, u2 %s' % (p1,u1,p2,u2))
        #print('distance between these axes should be 1')
        d_fmin = distance_between_axes_fmin(p1,u1,p2,u2)
        self.assertClose( d_fmin, 1 )
        self.assertClose( distance_between_axes(p1,u1,p2,u2), d_fmin )

        #randomly generated u1 and u2
        u1 = rand(3)
        u2 = rand(3)
        self.assertClose(
            distance_between_axes_fmin(p1,u1,p2,u2),
            distance_between_axes(p1,u1,p2,u2)
        )
        u1 = u2
        self.assertClose(
            distance_between_axes_fmin(p1,u1,p2,u2),
            distance_between_axes(p1,u1,p2,u2)
        )

    def test_rotation_matrix_to_euler_ZYX( self ) :
        from lib3D import euler_ZYX_rotation_matrix, rotation_matrix_to_euler_ZYX, rotation_matrix_to_euler_ZYX_check_answer
        R = [] #test rotation matrixes
        for i in range(6):
            R.append(  euler_ZYX_rotation_matrix( *(-pi + 2*pi*rand(3))) )
        R.append( numpy.eye(3) )
        R.append( numpy.array([[0,1,0],[0,0,1],[1,0,0.0]] ) )
        for i in range(3): #special case, angle2 = +-pi/2
            # euler_ZYX_rotation_matrix reduces
            #   [     0  , -s_1  , c_1*s_2 ],
            #   [     0  ,  c_1  , s_1*s_2 ],
            #   [ - s_2  ,    0  ,       0 ] ,
            # as angle1 and angle3 act about the same axis
            theta = -pi + 2*pi*rand()
            c, s = cos(theta),sin(theta)
            s_2 = numpy.sign(rand()-0.5)
            R.append( numpy.array([
                [0,-s,c*s_2],
                [0,c,s*s_2],
                [-s_2,0,0]]
            ) )
        #adding potential problem child
        R.append(numpy.array([[ -5.53267945e-05,   1.20480726e-17,   9.99999998e-01],
                              [  1.49015967e-08,   1.00000000e+00,   8.24445531e-13],
                              [ -9.99999998e-01,   1.49015967e-08,  -5.53267945e-05]]) )
        R.append(  euler_ZYX_rotation_matrix( -pi + 2*pi*rand(), pi/2,  -pi + 2*pi*rand() ) )
        R.append(  euler_ZYX_rotation_matrix( -pi + 2*pi*rand(), -pi/2,  -pi + 2*pi*rand() ) )
        for i, R_i in enumerate( R ):
            self.assertAllClose( dot(R_i, R_i.transpose()), numpy.eye(3) ) #rotation matrix transpose should equal its inverse
            #print('  test case %i' % i)
            #prettyPrintArray(R_i, ' '*4,'%1.2e')
            #print('  R_i * R_i.transpose():')
            #prettyPrintArray(dotProduct(R_i,R_i.transpose()), ' '*4)
            angle1, angle2, angle3 = rotation_matrix_to_euler_ZYX( R_i )
            rotation_matrix_to_euler_ZYX_check_answer( R_i, angle1, angle2, angle3 )

    def test_rotation_matrix_axis_and_angle( self ):
        from lib3D import rotation_matrix_axis_and_angle
        import pickle
        R = []
        R.append(numpy.array([[  1.00000000e+00,  -7.56401164e-10,   1.13448265e-17],
                              [  7.56401164e-10,   1.00000000e+00,   1.74357771e-17],
                              [ -1.13448265e-17,  -1.74357771e-17,   1.00000000e+00]]))
        R.append(numpy.array([[ -1.00000000e+00,   1.58333754e-16,   8.65956056e-17],
                                  [  1.58333754e-16,   1.00000000e+00,  -8.49830835e-16],
                                  [ -8.65956056e-17,  -1.29392004e-15,  -1.00000000e+00]]))
        R.append(numpy.array([[ -1.00000000e+00,   1.14448718e-16,  -2.01350825e-16],
                                  [ -1.14448718e-16,  -1.00000000e+00,   5.55111512e-17],
                                  [ -2.01350825e-16,   0.00000000e+00,   1.00000000e+00+1e-12]]))
        R.append(pickle.loads("cnumpy.core.multiarray\n_reconstruct\np0\n(cnumpy\nndarray\np1\n(I0\ntp2\nS'b'\np3\ntp4\nRp5\n(I1\n(I3\nI3\ntp6\ncnumpy\ndtype\np7\n(S'f8'\np8\nI0\nI1\ntp9\nRp10\n(I3\nS'<'\np11\nNNNI-1\nI-1\nI0\ntp12\nbI00\nS'\\x00\\x00\\x00\\x00\\x00\\x00\\xf0\\xbf8\\xa1\\x1f\\xba\\xe7E\\x94\\xbci\\x99\\x86\\xf4d\\xb4\\xa1\\xbc@NS\\xdfy\\xf6\\xa3<h\\x95\\xfa\\x18\\x91H\\xe5\\xbf\\xf2\\n\\xeb\\xdeY\\xe5\\xe7\\xbft\\x85\\xf5+\\n\\xd3\\x80\\xbc\\xf4\\n\\xeb\\xdeY\\xe5\\xe7\\xbfi\\x95\\xfa\\x18\\x91H\\xe5?'\np13\ntp14\nb."))
        for i, R_i in enumerate( R ):
            self.assertAllClose( dot(R_i, R_i.transpose()), numpy.eye(3) )
            #prettyPrintArray(R, ' '*4,'%1.2e')
            rotation_matrix_axis_and_angle(R_i, checkAnswer=True, debug=False)#i==len(testCases)-1)

    def test_plane_degrees_of_freedom( self ):
        from lib3D import plane_degrees_of_freedom, plane_degrees_of_freedom_check_answer
        R = []
        R.append( numpy.ones(3) / 3**0.5 )
        R.append( numpy.array([1.0, 0.0, 0.0]) )
        R.append( numpy.array([0.0, 1.0, 0.0]) )
        R.append( numpy.array([0.0, 0.0, 1.0]) )
        for i in range(6):
            r = -1 + 2*rand(3)
            r = r / norm(r)
            R.append(r)
        for i,normalVector in enumerate(R):
            #print('  testing on normal vector %s' % normalVector)
            d1, d2  = plane_degrees_of_freedom( normalVector, debug=False)
            plane_degrees_of_freedom_check_answer( normalVector, d1, d2, disp=False) 


    def generate_axes_pairs( self ):
        R = []
        R.append( [ numpy.array([1.0, 0.0, 0.0]), numpy.array([0.0, 1.0, 0.0]) ] )
        R.append( [ numpy.array([0.0, 1.0, 0.0]), numpy.array([0.0, 0.0, 1.0]) ] )
        R.append( [ numpy.array([1.0, 0.0, 0.0]), numpy.array([0.0, 0.0, 1.0]) ] )
        for i in range(3):
            r1, r2 = -1 + 2*rand(3), -1 + 2*rand(3)
            R.append( [ r1 / norm(r1), r2 / norm(r2) ] )
        return R
            
    def testing_planeIntersection( self ):
        from lib3D import planeIntersection, planeIntersection_check_answer
        for i,normalVectors in enumerate( self.generate_axes_pairs() ):
            #print('  testing on %s, %s' % (normalVectors[0], normalVectors[1]) )
            d = planeIntersection( normalVectors[0], normalVectors[1], debug=False)
            planeIntersection_check_answer( normalVectors[0], normalVectors[1], d,  disp=False, tol=10**-12)
            #print('all %i test cases passed.' % len(testCases)) 

    def test_AxisRotationDegreeOfFreedom_schemes( self ):
        '''
        Testing AxisRotationDegreeOfFreedom schemes, for find 1 rotation which is equivalent of 2
        a) matrix approach - where the rotation matrix are multiplied together, then axis and angle determined from that matrix
        b)quaternion approach - where quaterions multipled together, and then axis and angle determined from result.
        '''
        from lib3D import plane_degrees_of_freedom,  axis_rotation_matrix, rotation_matrix_axis_and_angle, quaternion2, quaternion_multiply, quaternion_to_axis_and_angle
        for i,axes in enumerate( self.generate_axes_pairs() ):
            axis1, axis4 = axes
            axis2, axis3  = plane_degrees_of_freedom(axis1)
            angle1, angle2 = (rand(2)-0.5)*2*pi
            #print('  rotation axes: %s, %s, angle1 %1.3f rad, angle2 %1.3f rad' % (axis1, axis2, angle1, angle2) )
            R_desired = dot( axis_rotation_matrix( angle2, *axis2), axis_rotation_matrix( angle1, *axis1) )
            axis_eqv, angle_eqv = rotation_matrix_axis_and_angle(R_desired)
            self.assertAllClose(
                R_desired,
                axis_rotation_matrix(angle_eqv, *axis_eqv)
            )
            q0,q1,q2,q3 = quaternion_multiply( quaternion2(angle2, *axis2),  quaternion2(angle1, *axis1))
            axis_eqv, angle_eqv = quaternion_to_axis_and_angle( q1, q2, q3, q0 )
            self.assertAllClose(
                R_desired,
                axis_rotation_matrix(angle_eqv, *axis_eqv)
            )

    def test_rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( self ):
        from lib3D import rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector, normalize, axis_rotation_matrix, quaternion, quaternion_rotation
        A = self.generate_axes_pairs()
        A.append( [[ 1.00000000e+00, -1.51981276e-16, -1.12027056e-17], [1.0, 0.0, 0.0 ]] )
        A.append( [[ -8.66025404e-01, 5.00000000e-01, -6.16297582e-33], [ -3.45126646e-31,   1.00000000e+00,  -1.22464680e-16]] )
        A.append( [[  6.79598526e-13,  -1.21896543e-12, 1.00000000e+00], [ 0.,  0.,  1.]] )

        for i,axes in enumerate(A):
            v, v_ref = axes
            v = normalize(v)
            v_ref = normalize(v_ref)
            axis, angle = rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector(v, v_ref)
            #print('  rotation axes: v_ref %s, v %s, axis %s, angle %1.3f rad' % (v_ref, v, axis, angle) )
            self.assertAllClose(
                v_ref,
                dot( axis_rotation_matrix( angle, *axis), v)
            )
            self.assertAllClose(
                v_ref,
                quaternion_rotation(v, *quaternion(angle, *axis))
            )

    def test_distance_between_axis_and_point( self ):
        from lib3D import normalize, distance_between_axis_and_point, distance_between_axis_and_point_old
        D = []
        for i in range(6):
            p1 = 10*rand(3)-5
            p2 = 10*rand(3)-5
            u1 = rand(3)
            D.append([p1, normalize(u1), p2])

        for i, D_i in enumerate( D ):
            p1,u1,p2 = D_i
            d_old = distance_between_axis_and_point( p1, u1, p2 )
            d_new = distance_between_axis_and_point_old( p1, u1, p2 )
            self.assertClose( d_old, d_new )
            #print('test case %i, distance old %f, distance new %f, diff %e' % (i+1, d_old, d_new, abs(d_old - d_new)))

    def test_gram_schmidt_orthonormalization( self ):
        from lib3D import gram_schmidt_orthonormalization
        V = [ [ numpy.array([1.0, 0.0, 0.0]), numpy.array([1.0,1.0,0]), numpy.array([1.0, 1.0, 1.0]) ] ]
        V = V + [ [rand(3)-0.5,rand(3)-0.5,rand(3)-0.5] for i in range(3) ]
        for vec1, vec2, vec3 in V:
            u1,u2,u3 = gram_schmidt_orthonormalization(vec1, vec2, vec3)
            U = numpy.array([u1,u2,u3])
            W =  dot(U, U.transpose())
            error = norm(W - numpy.eye(3)) 
            if error > 10**-9:
                print('FAILURE for Case:')
                print('   ', vec1, vec2, vec3)
                print('U:')
                prettyPrintArray(U, '  ', '%1.2f')
                print('U U^T:')
                prettyPrintArray( W, '  ', '%1.2f' )
            self.assertTrue(
                error < 10**-9,
                'gram_schmidt_orthonormalization test failed, error %e > 10**-9' % error
            )
    

if False:
    print('investigating trigonmetric function precission loss')
    angles = pi*(rand(12)-0.5)
    for angle in angles:
        print('   arccos(  cos(angle) ) - angle    %1.1e' % abs( arccos(  cos(angle) ) * numpy.sign(angle) - angle ) )
    for angle in angles:
        print('   arctan2( sin(angle), cos(angle)) - angle    %1.1e' % abs( arctan2( sin(angle), cos(angle)) - angle ) )
    for angle in angles:
        print('   1  - (sin(angle)**2 + cos(angle)**2)     %1.1e' % abs( 1  - (sin(angle)**2 + cos(angle)**2 ) ) )


    
