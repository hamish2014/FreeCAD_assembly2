'''
library for 3D operations such as rotations.
'''

import numpy
from numpy import pi, sin, cos, arctan2, arcsin

def quaternion(theta, u_x, u_y, u_z):
    '''http://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation 
    returns q_1, q_2, q_3, q_0 as to match FreeCads, if wikipedias naming is used'''
    #assert u_x**2 + u_y**2 + u_z**2 == 1 # numeric round-off errors makes this inpractical
    return ( u_x*sin(theta/2), u_y*sin(theta/2), u_z*sin(theta/2), cos(theta/2) ) #seems to be compadiable with FreeCAD. NB order needs to be changed from that in FreeCAD 

def quaternion_to_euler( q_1, q_2, q_3, q_0): #order to match FreeCads, naming to match wikipedias
    '''
    http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions 
    for conversion to 3-1-3 Euler angles (dont know about this one, seems to me to be 3-2-1...)
    '''
    psi = arctan2( 2*(q_0*q_1 + q_2*q_3), 1 - 2*(q_1**2 + q_2**2) ) 
    phi =   arcsin( 2*(q_0*q_2 - q_3*q_1) )
    theta =   arctan2( 2*(q_0*q_3 + q_1*q_2), 1 - 2*(q_2**2 + q_3**2) )
    return theta, phi, psi # gives same anser as FreeCADs toEuler function

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

def euler_rotation(p, angle1, angle2, angle3, axis1=1, axis2=2, axis3=3 ):
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
        R = numpy.dot(R_i, R)
        #print(R)
    #print('generic euler_rotation R')
    #print(R)
    return numpy.dot(R, p)

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
    return numpy.dot(euler_ZYX_rotation_matrix( angle1, angle2, angle3 ), p)

def axis_rotation( p, theta, u_x, u_y, u_z ):
    ''' http://en.wikipedia.org/wiki/Rotation_matrix '''
    R = numpy.array( [
            [ cos(theta) + u_x**2 * ( 1 - cos(theta)) , u_x*u_y*(1-cos(theta)) - u_z*sin(theta) ,  u_x*u_z*(1-cos(theta)) + u_y*sin(theta) ] ,
            [ u_y*u_x*(1-cos(theta)) + u_z*sin(theta) , cos(theta) + u_y**2 * (1-cos(theta))    ,  u_y*u_z*(1-cos(theta)) - u_x*sin(theta )] ,
            [ u_z*u_x*(1-cos(theta)) - u_y*sin(theta) , u_z*u_y*(1-cos(theta)) + u_x*sin(theta)  ,  cos(theta) + u_z**2 * (1-cos(theta))   ]
            ])
    return numpy.dot(R, p)


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
    '''
    used for axial and circular edget constraints
    '''
    # generated using sympy 
    # > t, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z = symbols('t, p1_x, p1_y, p1_z, p2_x, p2_y, p2_z, u1_x, u1_y, u1_z')
    # > d_sqrd = (p1_x + u1_x*t - p2_x)**2 + (p1_y + u1_y*t - p2_y)**2  + (p1_z + u1_z*t - p2_z)**2
    # > solve( diff( d_sqrd, t ), t ) # gives the expresssion for t_opt
    assert numpy.linalg.norm( u1 ) <> 0
    p1_x, p1_y, p1_z = p1
    u1_x, u1_y, u1_z = u1
    dist = 0
    for axis2_t in [-10, 0, 10]: #find point on axis 1 which is closest
        p2_x, p2_y, p2_z = p2 + axis2_t*u2
        t = (-p1_x*u1_x - p1_y*u1_y - p1_z*u1_z + p2_x*u1_x + p2_y*u1_y + p2_z*u1_z)/(u1_x**2 + u1_y**2 + u1_z**2)
        d_sqrd = (p1_x - p2_x + t*u1_x)**2 + (p1_y - p2_y + t*u1_y)**2 + (p1_z - p2_z + t*u1_z)**2
        dist = dist + d_sqrd
    return dist




if __name__ == '__main__':
    print('Testing lib3D.py')
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
    u = numpy.random.rand(3) - 0.5
    u = u / numpy.linalg.norm( u)
    #u = numpy.array([2**-0.5,0,2**-0.5])
    angle = pi * 2*(numpy.random.rand()-0.5)
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
    
    print('\nchecking distance_between_axes function')
    p1 = numpy.array( [0.0 , 0, 0 ] )
    u1 = numpy.array( [1.0 , 0, 0 ] )
    p2 = numpy.array( [1.0, 1.0, 1.0] )
    u2 = numpy.array( [  0 , 0, 1.0 ] )
    print('p1 %s, u1 %s, p2 %s, u2 %s' % (p1,u1,p2,u2))
    print('distance between these axes should be 1')
    print('  distance_between_axes_fmin :      %1.3f' % distance_between_axes_fmin(p1,u1,p2,u2))
    print('  distance_between_axes      :      %1.3f' % distance_between_axes(p1,u1,p2,u2))

    u1 = numpy.random.rand(3)
    u2 = numpy.random.rand(3)
    print('now testing with randomly generated u1 and u2')
    print('p1 %s, u1 %s, p2 %s, u2 %s' % (p1,u1,p2,u2))
    print('  distance_between_axes_fmin :      %1.6f' % distance_between_axes_fmin(p1,u1,p2,u2))
    print('  distance_between_axes      :      %1.6f' % distance_between_axes(p1,u1,p2,u2))
    print('setting u1 = u2')
    u1 = u2
    print('  distance_between_axes_fmin :      %1.6f' % distance_between_axes_fmin(p1,u1,p2,u2))
    print('  distance_between_axes      :      %1.6f' % distance_between_axes(p1,u1,p2,u2))
