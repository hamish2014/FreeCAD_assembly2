if __name__ == '__main__': #testomg.
    import sys
    sys.path.append('/usr/lib/freecad/lib/') #path to FreeCAD library on Linux
    import FreeCADGui
    assert not hasattr(FreeCADGui, 'addCommand')
    FreeCADGui.addCommand = lambda x,y: 0

from lib3D import *
import numpy


maxStep_linearDisplacement = 10.0
class PlacementDegreeOfFreedom:
    def __init__(self, parentSystem, objName, object_dof):
        self.system = parentSystem
        self.objName = objName
        self.vM = parentSystem.variableManager
        self.ind = parentSystem.variableManager.index[objName] + object_dof
        if self.ind % 6 < 3:
            self.directionVector = numpy.zeros(3)
            self.directionVector[ self.ind % 6 ] = 1
    def getValue( self):
        return self.vM.X[self.ind]
    def setValue( self, value):
        self.vM.X[self.ind] = value
    def maxStep(self):
        if self.ind % 6 < 3:
            return maxStep_linearDisplacement
        else:
            return pi/5
    def rotational(self):
        return self.ind % 6 > 2
    def str(self, indent=''):
        return '%s<Placement DegreeOfFreedom %s-%s value:%f>' % (indent, self.objName, ['x','y','z','azimuth','elavation','rotation'][self.ind % 6], self.getValue())
    def __repr__(self):
        return self.str()


class LinearMotionDegreeOfFreedom:
    def __init__(self, parentSystem, objName):
        self.system = parentSystem
        self.objName = objName
        self.vM = parentSystem.variableManager
        self.objInd = parentSystem.variableManager.index[objName]
    def setDirection(self, directionVector):
        self.directionVector = directionVector
    def getValue( self ):
        i = self.objInd
        return dotProduct( self.directionVector, self.vM.X[i:i+3])
    def setValue( self, value):
        currentValue = self.getValue()
        correction = (value -currentValue)*self.directionVector
        i = self.objInd
        self.vM.X[i:i+3] = self.vM.X[i:i+3] + correction
    def maxStep(self):             
        return maxStep_linearDisplacement #inf
    def rotational(self):
        return False
    def str(self, indent=''):
        return '%s<LinearMotion DegreeOfFreedom %s direction:%s value:%f>' % (indent, self.objName, self.directionVector, self.getValue())
    def __repr__(self):
        return self.str()
   
def prettyPrintArray( A, indent='  ', fmt='%1.1e' ):
    def pad(t):
        return t if t[0] == '-' else ' ' + t
    for r in A:
        txt = '  '.join( pad(fmt % v) for v in r)
        print(indent + '[ %s ]' % txt)

class AxisRotationDegreeOfFreedom:
    '''
    calculate the rotation variables ( azi, ela, angle )so that
    R_effective = R_about_axis * R_to_align_axis
    where
      R = azimuth_elevation_rotation_matrix(azi, ela, theta )

    '''
    def __init__(self, parentSystem, objName):
        self.system = parentSystem
        self.vM = parentSystem.variableManager
        self.objName = objName
        self.objInd = self.vM.index[objName]
    def setAxis(self, axis, axis_r, check_R_to_align_axis=False):
        if not ( hasattr(self, 'axis') and numpy.array_equal( self.axis, axis )): #if to avoid unnessary updates.
            self.axis = axis
            axis2, angle2 = rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( axis_r, axis )
            self.R_to_align_axis = axis_rotation_matrix(  angle2, *axis2 )
            if check_R_to_align_axis:
                print('NOTE: checking AxisRotationDegreeOfFreedom self.R_to_align_axis')
                if norm(  dotProduct(self.R_to_align_axis, axis_r) - axis ) > 10**-12:
                    raise ValueError, " dotProduct(self.R_to_align_axis, axis_r) - axis ) [%e] > 10**-12" % norm(  dotProduct(self.R_to_align_axis, axis_r) - axis )
            
            if not hasattr(self, 'x_ref_r'):
                self.x_ref_r, self.y_ref_r  =  plane_degrees_of_freedom( axis_r )
            else: #use gram_schmidt_orthonormalization ; import for case where axis close to z-axis, where numerical noise effects the azimuth angle used to generate plane DOF...
                notUsed, self.x_ref_r, self.y_ref_r = gram_schmidt_orthonormalization( axis_r,  self.x_ref_r, self.y_ref_r) #still getting wonky rotations :(
            self.x_ref = dotProduct(self.R_to_align_axis, self.x_ref_r) 
            self.y_ref = dotProduct(self.R_to_align_axis, self.y_ref_r) 

    def determine_R_about_axis(self, R_effective, checkAnswer=True, tol=10**-12): #not used anymore
        'determine R_about_axis so that R_effective = R_about_axis * R_to_align_axis'
        A = self.R_to_align_axis.transpose()
        X = numpy.array([
                numpy.linalg.solve(A, R_effective[row,:]) for row in range(3)
                ])
        #prettyPrintArray(X)
        if checkAnswer:
            print('  determine_R_about_axis: diff between R_effective and R_about_axis * R_to_align_axis (should be all close to zero):')
            error = R_effective - dotProduct(X, self.R_to_align_axis)
            assert norm(error) <= tol
        return X
        
    def vectorsAngleInDofsCoordinateSystem(self,v):
        return numpy.arctan2( 
                dotProduct(self.y_ref, v),
                dotProduct(self.x_ref, v),
                )

    def getValue( self, refApproach=True, tol=10**-7 ):
        i = self.objInd
        R_effective = azimuth_elevation_rotation_matrix( *self.vM.X[i+3:i+6] )
        if refApproach:
            v = dotProduct( R_effective, self.x_ref_r)
            if tol <> None and abs( dotProduct(v, self.axis) ) > tol:
                raise ValueError, "abs( dotProduct(v, self.axis) ) > %e [error %e]" % (tol, abs( dotProduct(v, self.axis) ))
            angle = self.vectorsAngleInDofsCoordinateSystem(v)
        else: 
            raise NotImplementedError,"does not work yet"
            R_effective = azimuth_elevation_rotation_matrix( *self.vM.X[i+3:i+6] )
            R_about_axis = self.determine_R_about_axis(R_effective)
            axis, angle =  rotation_matrix_axis_and_angle( R_about_axis )
            print( axis )
            print( self.axis )
            # does not work because   axis(R_about_axis) <> self.axis #which is damm weird if you ask me
        return angle
            
    def setValue( self, angle):
        R_about_axis = axis_rotation_matrix( angle, *self.axis )
        R = dotProduct(R_about_axis, self.R_to_align_axis)
        axis, angle = rotation_matrix_axis_and_angle( R )
        #todo, change to quaternions
        #Q2 = quaternion2( self.value, *self.axis )
        #q0,q1,q2,q3 = quaternion_multiply( Q2, self.Q1 )
        #axis, angle = quaternion_to_axis_and_angle( q1, q2, q3, q0 )
        azi, ela = axis_to_azimuth_and_elevation_angles(*axis)
        i = self.objInd
        self.vM.X[i+3:i+6] = azi, ela, angle

    def maxStep(self):             
        return pi/5
    def rotational(self):
        return True
    def str(self, indent=''):
        return '%s<AxisRotation DegreeOfFreedom %s axis:%s value:%f>' % (indent, self.objName, self.axis, self.getValue())
    def __repr__(self):
        return self.str()


if __name__ == '__main__':
    from numpy.random import rand
    import sys
    from variableManager import VariableManager
    print('Testing degrees-of-freedom library')

    print('creating test FreeCAD document, constraining a single Cube')
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
    print(box.Placement)

    class FakeSystem:
        def __init__(self, variableManager):
            self.variableManager = variableManager

    vM = VariableManager(FreeCAD.ActiveDocument)
    print(vM.X)
    constaintSystem = FakeSystem(vM)
    
    print('\nTesting PlacementDegreeOfFreedom')
    for object_dof in range(6):
        d = PlacementDegreeOfFreedom( constaintSystem, objName, object_dof )
        print(d)
        for i in range(6):
            value = pi*( rand() - 0.5 )
            d.setValue(value)
            assert d.getValue() == value

    print('\nTesting LinearMotionDegreeOfFreedom')
    tol = 10**-14
    for i in range(3):
        d = LinearMotionDegreeOfFreedom( constaintSystem, objName )
        d.setDirection( normalize(rand(3) - 0.5) )
        print(d)
        for i in range(12):
            value = 12*( rand() - 0.5 )
            d.setValue(value)
            returnedValue = d.getValue()
            if abs(returnedValue - value) > tol :
                raise ValueError,"d.getValue() - value <> %1.0e, [diff %e]" % (tol, returnedValue - value)

    print('\nTesting AxisRotationDegreeOfFreedom')
    tol = 10**-14
    for i in range(3):
        d = AxisRotationDegreeOfFreedom( constaintSystem, objName )
        axis_r =  normalize(rand(3) - 0.5) #axis in parts co-ordinate system (i.e. relative to part)
        axis = normalize(rand(3) - 0.5) # desired axis in global co-ordinate system
        d.setAxis(  axis, axis_r )
        d.setValue(0) #update azi,ela,theta to statify aligment of axis vector
        print(d)
        for i in range(6):
            value = 2*pi*( rand() - 0.5 )
            d.setValue(value)
            returnedValue = d.getValue()
            print('  d.getValue() %f value %f, diff %e' % (returnedValue, value, returnedValue - value))
            if abs(returnedValue - value) > tol :
                raise ValueError,"d.getValue() - value <> %1.0e, [diff %e]" % (tol, returnedValue - value)
