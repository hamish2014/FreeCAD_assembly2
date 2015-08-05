'''
library for 3D operations such as rotations.
'''

import numpy, pickle
from numpy import pi, sin, cos, arctan2, arcsin, arccos, dot, linspace, mean
from numpy.linalg import norm
dotProduct = numpy.dot
crossProduct = numpy.cross

def arcsin2( v, allowableNumericalError=10**-1 ):
    if -1 <= v and v <= 1:
        return arcsin(v)
    elif abs(v) -1 < allowableNumericalError:
        return pi/2 if v > 0 else -pi/2
    else:
        raise ValueError,"arcsin2 called with invalid input of %s" % v

def arccos2( v, allowableNumericalError=10**-1 ):
    if -1 <= v and v <= 1:
        return arccos(v)
    elif abs(v) -1 < allowableNumericalError:
        return 0 if v > 0 else pi
    else:
        raise ValueError,"arccos2 called with invalid input of %s" % v

def normalize( v ):
    return v / norm(v)


def quaternion(theta, u_x, u_y, u_z ):
    '''http://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation 
    returns q_1, q_2, q_3, q_0 as to match FreeCads, if wikipedias naming is used'''
    return ( u_x*sin(theta/2), u_y*sin(theta/2), u_z*sin(theta/2), cos(theta/2) )
def quaternion2(theta, u_x, u_y, u_z ):
    ''' returns in wikipedia order, i.e. cos(theta/2) element first '''
    return ( cos(theta/2), u_x*sin(theta/2), u_y*sin(theta/2), u_z*sin(theta/2) )

def quaternion_to_euler( q_1, q_2, q_3, q_0): #order to match FreeCads, naming to match wikipedias
    '''
    http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions 
    for conversion to 3-1-3 Euler angles (dont know about this one, seems to me to be 3-2-1...)
    '''
    psi = arctan2( 2*(q_0*q_1 + q_2*q_3), 1 - 2*(q_1**2 + q_2**2) ) 
    phi =   arcsin2( 2*(q_0*q_2 - q_3*q_1) )
    theta =   arctan2( 2*(q_0*q_3 + q_1*q_2), 1 - 2*(q_2**2 + q_3**2) )
    return theta, phi, psi # gives same answer as FreeCADs toEuler function

def quaternion_to_axis_and_angle(  q_1, q_2, q_3, q_0): 
    'http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions'
    q =  numpy.array( [q_1, q_2, q_3])
    if norm(q) > 0:
        return q/norm(q), 2*arccos2(q_0)
    else:
        return numpy.array([1.0,0,0]), 2*arccos2(q_0)

def azimuth_and_elevation_angles_to_axis( a, e):
    u_z = sin(e)
    u_x = cos(e)*cos(a)
    u_y = cos(e)*sin(a)
    return numpy.array([ u_x, u_y, u_z ])
def axis_to_azimuth_and_elevation_angles( u_x, u_y, u_z ):
    return arctan2( u_y, u_x), arcsin2(u_z)

def quaternion_multiply( q1, q2 ):
    'http://en.wikipedia.org/wiki/Quaternion#Hamilton_product'
    a_1, b_1, c_1, d_1 = q1
    a_2, b_2, c_2, d_2 = q2
    return numpy.array([
           a_1*a_2 - b_1*b_2 - c_1*c_2 - d_1*d_2,
           a_1*b_2 + b_1*a_2 + c_1*d_2 - d_1*c_2,
           a_1*c_2 - b_1*d_2 + c_1*a_2 + d_1*b_2,
           a_1*d_2 + b_1*c_2 - c_1*b_2 + d_1*a_2
           ])

def euler_to_quaternion(angle1, angle2, angle3, axis1=3, axis2=2, axis3=1):
    '''http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles '''
    Q = []
    for angle,axis in zip([angle1,angle2,angle3],[axis1,axis2,axis3]):
        q = numpy.array( [cos(angle/2),0,0,0 ] )
        q[axis] = sin(angle/2)
        Q.append(q)
    q = quaternion_multiply( Q[0], quaternion_multiply( Q[1], Q[2] ) )
    return q[1], q[2], q[3], q[0]

def quaternion_rotation(p, q_1, q_2, q_3, q_0 ):
    '''
    rotate the vector p using the quaternion u
    http://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    '''
    q =     numpy.array( [q_0,  q_1,  q_2,  q_3] ) 
    q_inv = numpy.array( [q_0, -q_1, -q_2, -q_3] ) 
    p_q =   numpy.array( [  0, p[0], p[1], p[2]] ) #p as a quaternion
    p_q_rotated = quaternion_multiply( q, quaternion_multiply( p_q, q_inv ) )
    #print( p_q_rotated )
    return p_q_rotated[1:]

def euler_rotation(p, angle1, angle2, angle3, axis1=3, axis2=2, axis3=3 ):
    ''' http://en.wikipedia.org/wiki/Rotation_matrix ,
    axis1=1, axis2=2, axis3=3 is the same as euler_ZYX_rotation'''
    R = numpy.eye(3)
    for angle,axis in zip([angle1,angle2,angle3],[axis1,axis2,axis3]):
        s = sin(angle)
        c = cos(angle)
        if axis == 1: #x rotation
            R_i = numpy.array([ [ 1, 0, 0], [ 0, c,-s], [ 0, s, c] ])
        elif axis == 2: # y rotation
            R_i = numpy.array([ [ c, 0, s], [ 0, 1, 0], [-s, 0, c] ])
        else: #z rotation
            R_i = numpy.array([ [ c,-s, 0], [ s, c, 0], [ 0, 0, 1] ])
        #print(R_i)
        R = dotProduct(R_i, R)
        #print(R)
    #print('generic euler_rotation R')
    #print(R)
    return dotProduct(R, p)

def euler_ZYX_rotation_matrix( angle1, angle2, angle3 ):
    ''' http://en.wikipedia.org/wiki/Rotation_matrix '''
    c_1, s_1 = cos(angle1), sin(angle1)
    c_2, s_2 = cos(angle2), sin(angle2)
    c_3, s_3 = cos(angle3), sin(angle3)
    return numpy.array( [
        [ c_1*c_2 , c_1*s_2*s_3 - c_3*s_1 , s_1*s_3 + c_1*c_3*s_2 ],
        [ c_2*s_1 , c_1*c_3 + s_1*s_2*s_3 , c_3*s_1*s_2 - c_1*s_3 ],
        [ - s_2   , c_2*s_3 , c_2*c_3 ]
    ])
    
def euler_ZYX_rotation(p, angle1, angle2, angle3 ):
    return dotProduct(euler_ZYX_rotation_matrix( angle1, angle2, angle3 ), p)

def axis_rotation_matrix( theta, u_x, u_y, u_z ):
    ''' http://en.wikipedia.org/wiki/Rotation_matrix '''
    return numpy.array( [
            [ cos(theta) + u_x**2 * ( 1 - cos(theta)) , u_x*u_y*(1-cos(theta)) - u_z*sin(theta) ,  u_x*u_z*(1-cos(theta)) + u_y*sin(theta) ] ,
            [ u_y*u_x*(1-cos(theta)) + u_z*sin(theta) , cos(theta) + u_y**2 * (1-cos(theta))    ,  u_y*u_z*(1-cos(theta)) - u_x*sin(theta )] ,
            [ u_z*u_x*(1-cos(theta)) - u_y*sin(theta) , u_z*u_y*(1-cos(theta)) + u_x*sin(theta) ,              cos(theta) + u_z**2*(1-cos(theta))   ]
            ])

def axis_rotation( p, theta, u_x, u_y, u_z ):
    return dotProduct(axis_rotation_matrix( theta, u_x, u_y, u_z ), p)

def azimuth_elevation_rotation_matrix(azi, ela, theta ):
    #print('azimuth_and_elevation_angles_to_axis(azi, ela) %s' % azimuth_and_elevation_angles_to_axis(azi, ela))
    return axis_rotation_matrix( theta, *azimuth_and_elevation_angles_to_axis(azi, ela))

def azimuth_elevation_rotation( p, azi, ela, theta ):
    return dotProduct(azimuth_elevation_rotation_matrix( azi, ela, theta ), p)

def rotation_matrix_to_euler_ZYX(R, debug=False, checkAnswer=False, tol=10**-6, tol_XZ_same_axis=10**-9 ):
    'better way available at http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions#Rotation_matrix_.E2.86.94_Euler_angles'
    if 1.0 - abs(R[2,0]) > tol_XZ_same_axis :
        s_2 = -R[2,0]
        for angle2 in [ arcsin2(s_2), pi - arcsin2(s_2)]:#two options
            if debug: print('         angle2 %f' % angle2)
            c_2 = cos(angle2)
            s_3 = R[2,1] / c_2
            c_3 = R[2,2] / c_2
            for angle3 in [ arcsin2(s_3),  pi - arcsin2(s_3)]:
                if debug: print('         angle2 %f, angle3 %f' % (angle2, angle3))
                if abs(cos(angle3) - c_3) < tol:
                    c_1 = max( min( R[0,0] / c_2, 1), -1)
                    #c_1 = R[0,0] / c_2
                    s_1 = R[1,0] / c_2
                    for angle1 in [arccos2(c_1), -arccos2(c_1)]:
                        if debug: print('         angle2 %f, angle3 %f, angle1 %f' % (angle2, angle3, angle1))
                        if abs(s_1 - sin(angle1)) < tol:
                            if checkAnswer: rotation_matrix_to_euler_ZYX_check_answer( R, angle1, angle2, angle3)
                            return angle1, angle2, angle3
        #otherwise try axis orientated approach
        if debug: print('rotation_matrix_to_euler_ZYX - direct appoarch failed. Parsing to rotation_matrix_to_euler_ZYX_2')
        return  rotation_matrix_to_euler_ZYX_2(R, debug)
    else:
        s_2 = -R[2,0]
        angle2 = arcsin2(s_2)
        c_2 = 0
        debug = False
        #return  rotation_matrix_to_euler_ZYX_2(R, debug)
        # euler_ZYX_rotation_matrix reduces to numpy.array( [
        #   [ c_1*c_2 , c_1*s_2*s_3 - c_3*s_1 , s_1*s_3 + c_1*c_3*s_2 ],
        #   [ c_2*s_1 , c_1*c_3 + s_1*s_2*s_3 , c_3*s_1*s_2 - c_1*s_3 ],
        #   [ - s_2   , c_2*s_3 , c_2*c_3 ]
        #which reduces to 
        #   [ 0     , s_2*c_1*s_3 -     s_1*c_3 ,     s_1*s_3 + s_2*c_1*c_3 ],
        #   [ 0     ,     c_1*c_3 + s_2*s_1*s_3 , s_1*c_3*s_2 -     c_1*s_3 ],
        #   [ - s_2,                           0,                          0]
        # triometric indeties
        #   sin (angle1 + angle3) = s_1 c_3 + c_1 s_3
        #   cos (angle1 + angle3)=  c_1 c_3 - s_1 s_3
        # making angle3 negative:
        #   sin (angle1 - angle3)=  s_1 c_3 - c_1 s_3 
        #   cos (angle1 - angle3)=  c_1 c_3 + s_1 s_3
        # let a = angle1 + angle3
        # let b = angle1 - angle3
        # elif s_2 == -1, R[1:,1:] reduces to
        #   [   sin(a),    -cos(a) ],
        #   [   cos(a),     sin(a) ], so
        # WTF are angle1 and angle3, about the same axis!? 
        # Which makes sense since Y-axis rotation, mean x-angle and z-angle are applied about the same axis. so let
        angle3 = 0 #s_3 -> 0 c_3 -> 1
        # euler_ZYX_rotation_matrix reduces
        #   [     0  , -s_1  , c_1*s_2 ],
        #   [     0  ,  c_1  , s_1*s_2 ],
        #   [ - s_2  ,    0  ,       0 ]
        for angle1 in [ arcsin2(-R[0,1]), pi - arcsin2(-R[0,1]) ]:
                if debug: print('         angle2 %f, angle1 %f, angle3 %f' % (angle2, angle1, angle3))
                #if debug: print('         cos(angle1) %f, R[0,2] %f' % (cos(angle1), R[0,2]))
                if abs(cos(angle1) - R[0,2]/s_2) < tol:
                    return angle1, angle2, angle3
        if debug: print('rotation_matrix_to_euler_ZYX - direct appoarch failed. Parsing to rotation_matrix_to_euler_ZYX_2')
        return  rotation_matrix_to_euler_ZYX_2(R, debug)
def rotation_matrix_to_euler_ZYX_check_answer( R, angle1, angle2, angle3, tol=10**-8, disp=False):
    R_out =  euler_ZYX_rotation_matrix( angle1, angle2, angle3)
    error = numpy.linalg.norm(R - R_out)
    if disp:
        print('rotation_matrix_to_euler_ZYX_check_answer:')
        print('    norm(R - euler_ZYX_rotation_matrix( angle1, angle2, angle3)) %e' % error)
    if error > tol:
         raise RuntimeError,'rotation_matrix_to_euler_ZYX check failed!. locals %s' % locals()
def rotation_matrix_to_euler_ZYX_2(R, debug=False):
    axis, angle = rotation_matrix_axis_and_angle_2(R)
    q_1, q_2, q_3, q_0 = quaternion(angle, *axis)
    return quaternion_to_euler( q_1, q_2, q_3, q_0)

def rotation_matrix_axis_and_angle(R, debug=False, checkAnswer=True, errorThreshold=10**-7, angle_pi_tol = 10**-5):
    'http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions#Rotation_matrix_.E2.86.94_Euler_axis.2Fangle'
    a = arccos2( 0.5 * ( R[0,0]+R[1,1]+R[2,2] - 1) )
    if abs(a % pi) > angle_pi_tol and abs(pi - (a % pi)) > angle_pi_tol:
        msg='checking angles sign, angle %f' % a
        for angle in [a, -a]:
            u_x = 0.5* (R[2,1]-R[1,2]) / sin(angle) 
            u_y = 0.5* (R[0,2]-R[2,0]) / sin(angle) 
            u_z = 0.5* (R[1,0]-R[0,1]) / sin(angle)
            if abs( (1-cos(angle))*u_x*u_y - u_z*sin(angle) - R[0,1] ) < errorThreshold:
                msg = 'abs( (1-cos(angle))*u_x*u_y - u_z*sin(angle) - R[0,1] ) < 10**-6 check passed' 
                break
        axis = numpy.array([u_x, u_y, u_z])
        error  = norm(axis_rotation_matrix(angle, *axis) - R)
        if debug: print('  norm(axis_rotation_matrix(angle, *axis) - R) %1.2e' % error)
        if error > errorThreshold:
            axis, angle = rotation_matrix_axis_and_angle_2(R, errorThreshold=errorThreshold, debug=debug, msg=msg)
    else:
        msg = 'abs(a % pi) > angle_pi_tol and abs(pi - (a % pi)) > angle_pi_tol'
        axis, angle = rotation_matrix_axis_and_angle_2( R, errorThreshold=errorThreshold, debug=debug, msg=msg)
    if numpy.isnan( angle ):
        raise RuntimeError,'locals %s' % locals() 
    return axis, angle
def rotation_matrix_axis_and_angle_2(R, debug=False, errorThreshold=10**-7, msg=None):
    w, v = numpy.linalg.eig(R) #this method is not used at the primary method as numpy.linalg.eig does not return answers in high enough precision
    angle, axis = None, None
    eigErrors = abs(w -1) #errors from 1+0j
    i = (eigErrors == min(eigErrors)).tolist().index(True)
    axis = numpy.real(v[:,i])
    if i <> 1:
        angle = arccos2(  numpy.real( w[1] ) )
    else:
        angle = arccos2(  numpy.real( w[0] ) )
    error  = norm(axis_rotation_matrix(angle, *axis) - R)
    if debug: print('rotation_matrix_axis_and_angle error %1.1e' % error)
    if error > errorThreshold:
        angle = -angle
        error = norm(axis_rotation_matrix(angle, *axis) - R)
        if error > errorThreshold:
            R_pickle_str = pickle.dumps(R)
            #R_abs_minus_identity = abs(R) - numpy.eye(3)
            print(R*R.transpose())
            raise ValueError, 'rotation_matrix_axis_and_angle_2: no solution found! locals %s' % str(locals())
    return axis, angle


def plane_degrees_of_freedom( normalVector, debug=False, checkAnswer=False ):
    a,e = axis_to_azimuth_and_elevation_angles(*normalVector)
    dof1 = azimuth_and_elevation_angles_to_axis( a, e - pi/2)
    dof2 = azimuth_and_elevation_angles_to_axis( a+pi/2, 0)
    if checkAnswer: plane_degrees_of_freedom_check_answer( normalVector, dof1, dof2, debug )
    return dof1, dof2
def plane_degrees_of_freedom_check_answer( normalVector, d1, d2, disp=False, tol=10**-12):
    if disp: 
        print('checking plane_degrees_of_freedom result')
        print('  plane normal vector   %s' % normalVector)
        print('  plane dof1            %s' % d1)
        print('  plane dof2            %s' % d2)
    Q = numpy.array([normalVector,d1,d2])
    P = dotProduct(Q,Q.transpose())
    error = norm(P - numpy.eye(3))
    if disp: 
        print('  dotProduct( array([normalVector,d1,d2]), array([normalVector,d1,d2]).transpose():')
        print(P)
        print(' error norm from eye(3) : %e' % error)
    if error > tol:
        raise RuntimeError,'plane_degrees_of_freedom check failed!. locals %s' % locals()

def planeIntersection( normalVector1, normalVector2, debug=False, checkAnswer=False ):
    return normalize ( crossProduct(normalVector1, normalVector2) )

def planeIntersection_check_answer( normalVector1, normalVector2, d,  disp=False, tol=10**-12):
    if disp:
        print('checking planeIntersection result')
        print('  plane normal vector 1 : %s' % normalVector1 )
        print('  plane normal vector 2 : %s' % normalVector2 )
        print('  d  : %s' % d )
    for t in [-3, 7, 12]:
        error1 = abs(dotProduct( normalVector1, d*t ))
        error2 = abs(dotProduct( normalVector2, d*t ))
        if disp:print('    d*(%1.1f) -> error1 %e, error2 %e' % (t, error1, error2) )
        if error1 > tol or error2 > tol:
            raise RuntimeError,' planeIntersection check failed!. locals %s' % locals()



def distance_between_axes( p1, u1, p2, u2):
    '''
    returns the shortest distance between to axes (or lines) in 3D space,
    where p1 is a point which line 1 goes through, and u1 is the direction vector for line 1.

    prob.
       minize d**2
       where d**2 = (p1_x + u1_x*t1 - p2_x - u2_x*t2)**2 + (p1_y + u1_y*t1 - p2_y - u2_y*t2)**2  + (p1_z + u1_z*t1 - p2_z - u2_z*t2)**2 
       giving a quadratic 2 varaiable (X = [t1,t2]) problem in the form of
           0.5 X^T A X + C^T B 
       differenting it gives
          0 = Q X + C
    
    using sympy to expand the abover expression
    > from sympy import *
    > x,y = symbols('x y')
    > expand( (x +y )**2)
      x**2 + 2*x*y + y**2
       
    > t1, t2, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z, u2_x, u2_y, u2_z = symbols('t1, t2, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z, u2_x, u2_y, u2_z')
    > d_sqrd = (p1_x + u1_x*t1 - p2_x - u2_x*t2)**2 + (p1_y + u1_y*t1 - p2_y - u2_y*t2)**2  + (p1_z + u1_z*t1 - p2_z - u2_z*t2)**2
    > expand(d_sqrd)
    > collect( expand(d_sqrd), [t1 , t2] )
    '''
    p1_x, p1_y, p1_z = p1
    u1_x, u1_y, u1_z = u1
    p2_x, p2_y, p2_z = p2
    u2_x, u2_y, u2_z = u2

    if numpy.array_equal( u1, u2 ) or numpy.array_equal( u1, -u2 ): #then
        assert numpy.linalg.norm( u1 ) <> 0
        # generated using sympy 
        # > t, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z = symbols('t, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z')
        # > d_sqrd = (p1_x + u1_x*t - p2_x)**2 + (p1_y + u1_y*t - p2_y)**2  + (p1_z + u1_z*t - p2_z)**2
        # > solve( diff( d_sqrd, t ), t ) # gives the expresssion for t_opt
        t = (-p1_x*u1_x - p1_y*u1_y - p1_z*u1_z + p2_x*u1_x + p2_y*u1_y + p2_z*u1_z)/(u1_x**2 + u1_y**2 + u1_z**2)
        d_sqrd = (p1_x - p2_x + t*u1_x)**2 + (p1_y - p2_y + t*u1_y)**2 + (p1_z - p2_z + t*u1_z)**2 
    else:
        t1_t1_coef = u1_x**2 + u1_y**2 + u1_z**2 #collect( expand(d_sqrd), [t1 , t2] )
        t1_t2_coef = -2*u1_x*u2_x - 2*u1_y*u2_y - 2*u1_z*u2_z # collect( expand(d_sqrd), [t1*t2] )
        t2_t2_coef = u2_x**2 + u2_y**2 + u2_z**2
        t1_coef    = 2*p1_x*u1_x + 2*p1_y*u1_y + 2*p1_z*u1_z - 2*p2_x*u1_x - 2*p2_y*u1_y - 2*p2_z*u1_z
        t2_coef    =-2*p1_x*u2_x - 2*p1_y*u2_y - 2*p1_z*u2_z + 2*p2_x*u2_x + 2*p2_y*u2_y + 2*p2_z*u2_z

        A = numpy.array([ [ 2*t1_t1_coef , t1_t2_coef ] , [ t1_t2_coef, 2*t2_t2_coef ] ])
        b = numpy.array([ t1_coef, t2_coef])
        try:
            t1, t2 = numpy.linalg.solve(A,-b)
        except numpy.linalg.LinAlgError:
            print('distance_between_axes, failed to solve problem due to LinAlgError, using numerical solver instead')
            print('  variables : ')
            print('    p1 : %s' % p1 )
            print('    u1 : %s' % u1 )
            print('    p2 : %s' % p2 )
            print('    u2 : %s' % u2 )
            return distance_between_axes_fmin(p1, u1, p2, u2)
            
        d_sqrd = t1_t1_coef * t1**2 + t1_t2_coef * t1*t2 + t2_t2_coef * t2**2 + t1_coef*t1 + t2_coef*t2 + p1_x**2 - 2*p1_x*p2_x + p1_y**2 - 2*p1_y*p2_y + p1_z**2 - 2*p1_z*p2_z + p2_x**2 + p2_y**2 + p2_z**2 
    return d_sqrd ** 0.5

def distance_between_axes_fmin( p1, u1, p2, u2):
    from scipy.optimize import fmin_bfgs
    def distance(T):
        t1, t2 = T
        return numpy.linalg.norm( p1 + u1*t1 - (p2 + u2*t2) )
    T_opt = fmin_bfgs( distance, [0 , 0], disp=False)
    return distance(T_opt)

def distance_between_two_axes_3_points(p1,u1,p2,u2):
    ''' used for axial and circular edge constraints  '''
    # generated using sympy 
    # > t, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z = symbols('t, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z')
    # > d_sqrd = (p1_x + u1_x*t - p2_x)**2 + (p1_y + u1_y*t - p2_y)**2  + (p1_z + u1_z*t - p2_z)**2
    # > solve( diff( d_sqrd, t ), t ) # gives the expresssion for t_opt
    assert numpy.linalg.norm( u1 ) <> 0
    p1_x, p1_y, p1_z = p1
    u1_x, u1_y, u1_z = u1
    #if not (u1_x**2 + u1_y**2 + u1_z**2) == 1:
    #    raise ValueError, "(u1_x**2 + u1_y**2 + u1_z**2) <>1 but rather %f  " % ( u1_x**2 + u1_y**2 + u1_z**2 )
    dist = 0
    for axis2_t in [-10, 0, 10]: #find point on axis 1 which is closest
        p2_x, p2_y, p2_z = p2 + axis2_t*u2
        t = (-p1_x*u1_x - p1_y*u1_y - p1_z*u1_z + p2_x*u1_x + p2_y*u1_y + p2_z*u1_z)/(u1_x**2 + u1_y**2 + u1_z**2) #should be able to drop this last term as it will equal 1...
        d_sqrd = (p1_x - p2_x + t*u1_x)**2 + (p1_y - p2_y + t*u1_y)**2 + (p1_z - p2_z + t*u1_z)**2
        dist = dist + d_sqrd ** 0.5
    return dist

def distance_between_axis_and_point( p1,u1,p2 ):
    assert numpy.linalg.norm( u1 ) <> 0
    d = p2 - p1
    offset = d - dotProduct(u1,d)*u1
    #print(norm(offset))
    return norm(offset)

def distance_between_axis_and_point_old( p1, u1, p2 ):
    assert numpy.linalg.norm( u1 ) <> 0
    p1_x, p1_y, p1_z = p1
    u1_x, u1_y, u1_z = u1
    p2_x, p2_y, p2_z = p2
    t = (-p1_x*u1_x - p1_y*u1_y - p1_z*u1_z + p2_x*u1_x + p2_y*u1_y + p2_z*u1_z)
    # dropped the (u1_x**2 + u1_y**2 + u1_z**2) term as it should equal 1
    d_sqrd = (p1_x - p2_x + t*u1_x)**2 + (p1_y - p2_y + t*u1_y)**2 + (p1_z - p2_z + t*u1_z)**2
    return d_sqrd ** 0.5



def rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( v, v_ref ):
    c = crossProduct( v, v_ref)
    if norm(c) > 0:
        axis = normalize(c)
    else: #dont think this ever happens.
        axis, notUsed = plane_degrees_of_freedom( v )
    #if dof_axis == None:
    angle = arccos2( dotProduct( v, v_ref ))
    #else:
    #    axis3 = normalize ( crossProduct(v_ref, dof_axis) )
    #    a = dotProduct( v, v_ref ) #adjacent
    #    o = dotProduct( v, axis3 ) #oppersite
    #    angle = numpy.arctan2( o, a )
    return axis, angle

def rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector2( v, v_ref, dof_axis=None ):
    '''
    calculate the axis in a method other then a crossduct.
    finding axis, so that dot(axis, v) == 0 and dot(axis, v_ref) == 0, using linear alegebra.

    '''
    A_matrixs = []
    for i in range(3):
        A_matrixs.append([ 
                [v[j] for j in range(3) if j <> i],
                [v_ref[j] for j in range(3) if j <> i]] )
        #prettyPrintArray( A_matrixs[-1] )
    cond_number = map( numpy.linalg.cond,  A_matrixs)
    minloc = cond_number.index(min(cond_number)) 
    b = numpy.array([ -v[minloc], -v_ref[minloc] ])
    c = numpy.linalg.solve( A_matrixs[minloc], b).tolist()
    c.insert(minloc,1)
    c = numpy.array(c) #* numpy.sign(crossProduct( v, v_ref))
    if norm(c) > 0:
        axis = normalize(c)
    else: #dont think this ever happens.
        axis, notUsed = plane_degrees_of_freedom( v )
    if dof_axis == None:
        angle = arccos2( dotProduct( v, v_ref ))
        #checking if negative angle should be used
        v_rotated = dotProduct( axis_rotation_matrix( angle, *axis), v)
        #print('             v_rotated %s' % (v_rotated) )
        error = norm( v_ref - v_rotated )
        if error > 1:
            angle = -angle
    else:
        axis3 = normalize ( crossProduct(v_ref, dof_axis) )
        a = dotProduct( v, v_ref ) #adjacent
        o = dotProduct( v, axis3 ) #oppersite
        angle = numpy.arctan2( o, a )
    return axis, angle


def gram_schmidt_proj(u,v):
    return dot(v,u)/dot(u,u)*u
def gram_schmidt_orthonormalization( v1, v2, v3 ):
    'https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process'
    u1 = v1
    u2 = v2 - gram_schmidt_proj(u1,v2)
    u3 = v3 - gram_schmidt_proj(u1,v3) - gram_schmidt_proj(u2,v3)
    return normalize(u1), normalize(u2), normalize(u3)

def fit_plane_to_surface1( surface, n_u=3, n_v=3 ):
    uv = sum( [ [ (u,v) for u in linspace(0,1,n_u)] for v in linspace(0,1,n_v) ], [] )
    P = [ surface.value(u,v) for u,v in uv ] #positions at u,v points
    N = [ crossProduct( *surface.tangent(u,v) ) for u,v in uv ] 
    plane_norm = sum(N) / len(N) #plane's normal, averaging done to reduce error
    plane_pos = P[0]
    error = sum([ abs( dot(p - plane_pos, plane_norm) ) for p in P ])
    return plane_norm, plane_pos, error

def fit_rotation_axis_to_surface1( surface, n_u=3, n_v=3 ):
    'should work for cylinders and pssibly cones (depending on the u,v mapping)'
    uv = sum( [ [ (u,v) for u in linspace(0,1,n_u)] for v in linspace(0,1,n_v) ], [] )
    P = [ numpy.array(surface.value(u,v)) for u,v in uv ] #positions at u,v points
    N = [ crossProduct( *surface.tangent(u,v) ) for u,v in uv ] 
    intersections = []
    for i in range(len(N)-1):
        for j in range(i+1,len(N)):
            # based on the distance_between_axes( p1, u1, p2, u2) function,
            if 1 - abs(dot( N[i], N[j])) < 10**-6:
                continue #ignore parrallel case
            p1_x, p1_y, p1_z = P[i]
            u1_x, u1_y, u1_z = N[i]
            p2_x, p2_y, p2_z = P[j]
            u2_x, u2_y, u2_z = N[j]
            t1_t1_coef = u1_x**2 + u1_y**2 + u1_z**2 #should equal 1
            t1_t2_coef = -2*u1_x*u2_x - 2*u1_y*u2_y - 2*u1_z*u2_z # collect( expand(d_sqrd), [t1*t2] )
            t2_t2_coef = u2_x**2 + u2_y**2 + u2_z**2 #should equal 1 too
            t1_coef    = 2*p1_x*u1_x + 2*p1_y*u1_y + 2*p1_z*u1_z - 2*p2_x*u1_x - 2*p2_y*u1_y - 2*p2_z*u1_z
            t2_coef    =-2*p1_x*u2_x - 2*p1_y*u2_y - 2*p1_z*u2_z + 2*p2_x*u2_x + 2*p2_y*u2_y + 2*p2_z*u2_z
            A = numpy.array([ [ 2*t1_t1_coef , t1_t2_coef ] , [ t1_t2_coef, 2*t2_t2_coef ] ])
            b = numpy.array([ t1_coef, t2_coef])
            try:
                t1, t2 = numpy.linalg.solve(A,-b)
            except numpy.linalg.LinAlgError:
                continue #print('distance_between_axes, failed to solve problem due to LinAlgError, using numerical solver instead')
            pos_t1 = P[i] + numpy.array(N[i])*t1
            pos_t2 = P[j] + N[j]*t2
            intersections.append( pos_t1 )
            intersections.append( pos_t2 )
    if len(intersections) < 2:
        error = numpy.inf
        return 0, 0, error
    else: #fit vector to intersection points; http://mathforum.org/library/drmath/view/69103.html
        X = numpy.array(intersections)
        centroid = numpy.mean(X,axis=0)
        M = numpy.array([i - centroid for i in intersections ])
        A = numpy.dot(M.transpose(), M)
        U,s,V = numpy.linalg.svd(A)    #numpy docs: s : (..., K) The singular values for every matrix, sorted in descending order.
        axis_pos = centroid
        axis_dir = V[0]
        error = s[1] #dont know if this will work
        return axis_dir, axis_pos, error


if __name__ == '__main__':
    print('Testing lib3D.py')
    rand = numpy.random.rand

    print('\nRotations\n-----------\n')
    rotationTests = ( #FreeCAD Q, FreeCAD Q euler angles
        ( (0.2656567662671845, 0.25272127048434034, 0.7755360520891752, 0.5139088186548074), (109.54525270772452, -8.760320864783417, 42.29015715378342) ),
        ( (-0.26019046408365476, 0.6829999682195941, 0.19611613513818393, 0.6537204504606134), (-95.71059313749971, 84.2894068625003, -133.40658272845215) )
        )
    
    for Q, eulerAngles in rotationTests:
        print('FreeCAD Q : \t%s' % str(Q) )
        print('quaternion (Q) to euler angles:')
        print('  FreeCAD  \t%s' % str(eulerAngles) )
        print('  lib3D    \t%s' % str(tuple(numpy.array(quaternion_to_euler(*Q))/pi*180 )))
        print('euler angles to quaternion:')
        ang1, ang2, ang3 = numpy.array(eulerAngles)/180*pi
        print('  FreeCAD  \t%s' % str(Q) )
        print('  lib3D    \t%s' % str(euler_to_quaternion(ang1,ang2,ang3)))
        print('')

    print('checking that rotation using euler angles and rotation using quaterions gives the same results')
    p = numpy.array([1,2,3])
    print('p  %s' % p)
    u = rand(3) - 0.5
    u = u / numpy.linalg.norm( u)
    #u = numpy.array([2**-0.5,0,2**-0.5])
    angle = pi * 2*(rand()-0.5)
    print('rotation axis %s (norm %1.3f), angle %f rads' % (u, numpy.linalg.norm( u), angle) )
    p_r = axis_rotation(p, angle, *u )
    print('  axis_rotation :       %s   (norm(p) %1.3f, norm(p_rotated) %1.3f' % (p_r, numpy.linalg.norm(p), numpy.linalg.norm(p_r)))
    q_1, q_2, q_3, q_0 = quaternion(angle, *u)
    #print('norm of q %1.3f' % numpy.linalg.norm( [q_1, q_2, q_3, q_0 ] ))
    p_r = quaternion_rotation(p, q_1, q_2, q_3, q_0 )
    print('  quaternion_rotation : %s   (norm(p) %1.3f, norm(p_rotated) %1.3f' % (p_r, numpy.linalg.norm(p), numpy.linalg.norm(p_r)))
    ang1, ang2, ang3 = quaternion_to_euler(q_1, q_2, q_3, q_0)
    p_r = euler_ZYX_rotation( p, ang1, ang2, ang3)
    print('  euler_rotation :      %s   (norm(p) %1.3f, norm(p_rotated) %1.3f' % (p_r, numpy.linalg.norm(p), numpy.linalg.norm(p_r)))
    p_r = euler_rotation( p, ang1, ang2, ang3)
    print('  euler_rotation2 :     %s   (norm(p) %1.3f, norm(p_rotated) %1.3f' % (p_r, numpy.linalg.norm(p), numpy.linalg.norm(p_r)))
    

    print('\ntesting quaternion_to_axis_and_angle')
    testcases = []
    for r in numpy.eye(3):
        testcases.append( [r, 0.1 + rand() ] )
    for i in range(3):
        axis = rand(3) - 0.5
        testcases.append( [ axis/norm(axis), 0.5-rand() ] )
    for i,testcase in enumerate(testcases):
        axis, angle = testcase
        q_1, q_2, q_3, q_0  = quaternion(angle, *axis)
        axis_out, angle_out = quaternion_to_axis_and_angle(q_1, q_2, q_3, q_0)
        if numpy.sign( angle_out ) <> numpy.sign( angle):
            angle_out = -angle_out
            axis_out = -axis_out
        if norm(axis - axis_out) > 10**-12 or norm(angle - angle_out) > 10**-9:
            raise ValueError, "norm(axis - axis_out) > 10**-12 or norm(angle - angle_out) > 10**-9. \n  in:  axis %s, angle %s\n  out: axis %s, angle %s" % (axis,angle,axis_out,angle_out) 
    print('testing axis_to_azimuth_and_elevation_angles & azimuth_and_elevation_angles_to_axis')
    for i,testcase in enumerate(testcases):
        axis, angle = testcase
        a,e = axis_to_azimuth_and_elevation_angles(*axis)
        axis_out = azimuth_and_elevation_angles_to_axis( a, e)
        if norm(axis - axis_out) > 10**-12:
            raise ValueError, "norm(axis - axis_out) > 10**-12. \n  in:  axis %s \n  azimuth %f, elavation %f \n  out: axis %s" % (axis,a,e,axis_out)


    print('\nchecking distance_between_axes function')
    p1 = numpy.array( [0.0 , 0, 0 ] )
    u1 = numpy.array( [1.0 , 0, 0 ] )
    p2 = numpy.array( [1.0, 1.0, 1.0] )
    u2 = numpy.array( [  0 , 0, 1.0 ] )
    print('p1 %s, u1 %s, p2 %s, u2 %s' % (p1,u1,p2,u2))
    print('distance between these axes should be 1')
    print('  distance_between_axes_fmin :      %1.3f' % distance_between_axes_fmin(p1,u1,p2,u2))
    print('  distance_between_axes      :      %1.3f' % distance_between_axes(p1,u1,p2,u2))

    u1 = rand(3)
    u2 = rand(3)
    print('now testing with randomly generated u1 and u2')
    print('p1 %s, u1 %s, p2 %s, u2 %s' % (p1,u1,p2,u2))
    print('  distance_between_axes_fmin :      %1.6f' % distance_between_axes_fmin(p1,u1,p2,u2))
    print('  distance_between_axes      :      %1.6f' % distance_between_axes(p1,u1,p2,u2))
    print('setting u1 = u2')
    u1 = u2
    print('  distance_between_axes_fmin :      %1.6f' % distance_between_axes_fmin(p1,u1,p2,u2))
    print('  distance_between_axes      :      %1.6f' % distance_between_axes(p1,u1,p2,u2))


    def prettyPrintArray( A, indent='  ', fmt='%1.1e' ):
        def pad(t):
            return t if t[0] == '-' else ' ' + t
        for r in A:
            txt = '  '.join( pad(fmt % v) for v in r)
            print(indent + '[ %s ]' % txt)

    print('\ntesting rotation_matrix_to_euler_ZYX')
    testCases = []
    for i in range(6):
        testCases.append(  euler_ZYX_rotation_matrix( *(-pi + 2*pi*rand(3))) )
    testCases.append( numpy.eye(3) )
    testCases.append( numpy.array([[0,1,0],[0,0,1],[1,0,0.0]] ) )
    for i in range(3): #special case, angle2 = +-pi/2
        # euler_ZYX_rotation_matrix reduces
        #   [     0  , -s_1  , c_1*s_2 ],
        #   [     0  ,  c_1  , s_1*s_2 ],
        #   [ - s_2  ,    0  ,       0 ] , as angle1 and angle3 act about the same axis
        theta = -pi + 2*pi*rand()
        c, s = cos(theta),sin(theta)
        s_2 = numpy.sign(rand()-0.5)
        testCases.append( numpy.array([[0,-s,c*s_2],[0,c,s*s_2],[-s_2,0,0]] ) )
    #adding potential problem child
    testCases.append(numpy.array([[ -5.53267945e-05,   1.20480726e-17,   9.99999998e-01],
                                  [  1.49015967e-08,   1.00000000e+00,   8.24445531e-13],
                                  [ -9.99999998e-01,   1.49015967e-08,  -5.53267945e-05]]))
    testCases.append(  euler_ZYX_rotation_matrix( -pi + 2*pi*rand(), pi/2,  -pi + 2*pi*rand() ) )
    testCases.append(  euler_ZYX_rotation_matrix( -pi + 2*pi*rand(), -pi/2,  -pi + 2*pi*rand() ) )
    for i, R in enumerate( testCases ):
        #print('  test case %i' % i)
        #prettyPrintArray(R, ' '*4,'%1.2e')
        #print('  R * R.transpose():')
        #prettyPrintArray(dotProduct(R,R.transpose()), ' '*4)
        angle1, angle2, angle3 = rotation_matrix_to_euler_ZYX( R )
        rotation_matrix_to_euler_ZYX_check_answer(R, angle1, angle2, angle3)
        pass
    print('all %i rotation_matrix_to_euler_ZYX tests passed.' % len(testCases)) 

    print('\ntesting rotation_matrix_axis_and_angle')
    testCases.append(numpy.array([[  1.00000000e+00,  -7.56401164e-10,   1.13448265e-17],
                                  [  7.56401164e-10,   1.00000000e+00,   1.74357771e-17],
                                  [ -1.13448265e-17,  -1.74357771e-17,   1.00000000e+00]]))
    testCases.append(numpy.array([[ -1.00000000e+00,   1.58333754e-16,   8.65956056e-17],
                                  [  1.58333754e-16,   1.00000000e+00,  -8.49830835e-16],
                                  [ -8.65956056e-17,  -1.29392004e-15,  -1.00000000e+00]]))
    testCases.append(numpy.array([[ -1.00000000e+00,   1.14448718e-16,  -2.01350825e-16],
                                  [ -1.14448718e-16,  -1.00000000e+00,   5.55111512e-17],
                                  [ -2.01350825e-16,   0.00000000e+00,   1.00000000e+00+1e-12]]))
    testCases.append(pickle.loads("cnumpy.core.multiarray\n_reconstruct\np0\n(cnumpy\nndarray\np1\n(I0\ntp2\nS'b'\np3\ntp4\nRp5\n(I1\n(I3\nI3\ntp6\ncnumpy\ndtype\np7\n(S'f8'\np8\nI0\nI1\ntp9\nRp10\n(I3\nS'<'\np11\nNNNI-1\nI-1\nI0\ntp12\nbI00\nS'\\x00\\x00\\x00\\x00\\x00\\x00\\xf0\\xbf8\\xa1\\x1f\\xba\\xe7E\\x94\\xbci\\x99\\x86\\xf4d\\xb4\\xa1\\xbc@NS\\xdfy\\xf6\\xa3<h\\x95\\xfa\\x18\\x91H\\xe5\\xbf\\xf2\\n\\xeb\\xdeY\\xe5\\xe7\\xbft\\x85\\xf5+\\n\\xd3\\x80\\xbc\\xf4\\n\\xeb\\xdeY\\xe5\\xe7\\xbfi\\x95\\xfa\\x18\\x91H\\xe5?'\np13\ntp14\nb."))
    for i, R in enumerate( testCases ):
        #prettyPrintArray(R, ' '*4,'%1.2e')
        rotation_matrix_axis_and_angle(R, checkAnswer=True, debug=i==len(testCases)-1)
    print('all %i tests passed.' % len(testCases))  

    print('\ntesting plane_degrees_of_freedom')
    testCases = []
    testCases.append( numpy.ones(3) / 3**0.5 )
    testCases.append( numpy.array([1.0, 0.0, 0.0]) )
    testCases.append( numpy.array([0.0, 1.0, 0.0]) )
    testCases.append( numpy.array([0.0, 0.0, 1.0]) )
    for i in range(6):
        r = -1 + 2*rand(3)
        r = r / norm(r)
        testCases.append(r)
    for i,normalVector in enumerate(testCases):
        print('  testing on normal vector %s' % normalVector)
        d1, d2  = plane_degrees_of_freedom( normalVector, debug=False)
        plane_degrees_of_freedom_check_answer( normalVector, d1, d2, disp=True) 
    print('all %i plane_degrees_of_freedom tests passed.' % len(testCases)) 

    print('\ntesting planeIntersection')
    testCases = []
    testCases.append( [ numpy.array([1.0, 0.0, 0.0]), numpy.array([0.0, 1.0, 0.0]) ] )
    testCases.append( [ numpy.array([0.0, 1.0, 0.0]), numpy.array([0.0, 0.0, 1.0]) ] )
    testCases.append( [ numpy.array([1.0, 0.0, 0.0]), numpy.array([0.0, 0.0, 1.0]) ] )
    for i in range(3):
        r1, r2 = -1 + 2*rand(3), -1 + 2*rand(3)
        testCases.append( [ r1 / norm(r1), r2 / norm(r2) ] )
    for i,normalVectors in enumerate(testCases):
        print('  testing on %s, %s' % (normalVectors[0], normalVectors[1]) )
        d = planeIntersection( normalVectors[0], normalVectors[1], debug=False)
        planeIntersection_check_answer( normalVectors[0], normalVectors[1], d,  disp=False, tol=10**-12)
    print('all %i test cases passed.' % len(testCases)) 


    print('\nTesting AxisRotationDegreeOfFreedom schemes, for find 1 rotation which is equivalent of 2')
    print('  a) matrix approach - where the rotation matrix are multiplied together, then axis and angle determined from that matrix')
    print('  b) quaternion approach - where quaterions multipled together, and then axis and angle determined from result.')
    for i,axes in enumerate(testCases):
        axis1, axis4 = axes
        axis2, axis3  = plane_degrees_of_freedom(axis1)
        angle1, angle2 = (rand(2)-0.5)*2*pi
        print('  rotation axes: %s, %s, angle1 %1.3f rad, angle2 %1.3f rad' % (axis1, axis2, angle1, angle2) )
        R_desired = dotProduct( axis_rotation_matrix( angle2, *axis2), axis_rotation_matrix( angle1, *axis1) )
        axis_eqv, angle_eqv = rotation_matrix_axis_and_angle(R_desired)
        error = norm(R_desired - axis_rotation_matrix(angle_eqv, *axis_eqv))
        print('    matrix approach error  %1.2e' % error )
        q0,q1,q2,q3 = quaternion_multiply( quaternion2(angle2, *axis2),  quaternion2(angle1, *axis1))
        axis_eqv, angle_eqv = quaternion_to_axis_and_angle( q1, q2, q3, q0 )
        error = norm(R_desired - axis_rotation_matrix(angle_eqv, *axis_eqv))
        print('    quaternion approach error  %1.2e' % error )

    print('\nTesting rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector')
    testCases.append( [[ 1.00000000e+00, -1.51981276e-16, -1.12027056e-17], [1.0, 0.0, 0.0 ]] )
    testCases.append( [[ -8.66025404e-01, 5.00000000e-01, -6.16297582e-33], [ -3.45126646e-31,   1.00000000e+00,  -1.22464680e-16]] )
    testCases.append( [[  6.79598526e-13,  -1.21896543e-12, 1.00000000e+00], [ 0.,  0.,  1.]] )
    for i,axes in enumerate(testCases):
        v, v_ref = axes
        v = normalize(v)
        v_ref = normalize(v_ref)
        axis, angle = rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector(v, v_ref)
        #print('  rotation axes: v_ref %s, v %s, axis %s, angle %1.3f rad' % (v_ref, v, axis, angle) )
        v_rotated = dotProduct( axis_rotation_matrix( angle, *axis), v)
        #print('             v_rotated %s' % (v_rotated) )
        error = norm( v_ref - v_rotated )
        #print(norm(v)-1, norm(v_ref)-1)
        print('  matrix  v_ref %s, v %s, error %1.3e' % ( v, v_ref, error ) )


        v_rotated = quaternion_rotation(v, *quaternion(angle, *axis))
        #print('             v_rotated %s' % (v_rotated) )
        error = norm( v_ref - v_rotated )
        print('  quatrian  v_ref %s, v %s, error %1.3e' % ( v, v_ref, error ) )

        if error > 10**-9 :
            raise ValueError, 'Failure for v_ref %s, v %s, error %1.3e' % ( v, v_ref, error )
    print('all test case passed')

    print('distance between axis and point')
    testCases = []
    for i in range(6):
        p1 = 10*rand(3)-5
        p2 = 10*rand(3)-5
        u1 = rand(3)
        testCases.append([p1, normalize(u1), p2])

    for i,D in enumerate(testCases):
        p1,u1,p2 = D
        d_old = distance_between_axis_and_point( p1, u1, p2 )
        d_new = distance_between_axis_and_point_old( p1, u1, p2 )
        print('test case %i, distance old %f, distance new %f, diff %e' % (i+1, d_old, d_new, abs(d_old - d_new)))


    print('investigating trigonmetric function precission loss')
    angles = pi*(rand(12)-0.5)
    for angle in angles:
        print('   arccos(  cos(angle) ) - angle    %1.1e' % abs( arccos(  cos(angle) ) * numpy.sign(angle) - angle ) )
    for angle in angles:
        print('   arctan2( sin(angle), cos(angle)) - angle    %1.1e' % abs( arctan2( sin(angle), cos(angle)) - angle ) )
    for angle in angles:
        print('   1  - (sin(angle)**2 + cos(angle)**2)     %1.1e' % abs( 1  - (sin(angle)**2 + cos(angle)**2 ) ) )


    print('\ntesting gram_schmidt_orthonormalization')
    testCases = [ [ numpy.array([1.0, 0.0, 0.0]), numpy.array([1.0,1.0,0]), numpy.array([1.0, 1.0, 1.0]) ] ]
    testCases = testCases + [ [rand(3)-0.5,rand(3)-0.5,rand(3)-0.5] for i in range(3) ]
    for vec1, vec2, vec3 in testCases:
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
            raise ValueError, 'gram_schmidt_orthonormalization test failed, error %e > 10**-9' % error
    print('..passed')
