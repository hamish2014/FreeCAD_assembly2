'''
a constraint system consists of
 - one or more objects 
 - one or more constraints
 - 0 or more degrees-of-freedom

solver approach
  1. begin with fixed object, to create initial constraint system
  2. add constraints to the constraint system until all constraints are added
     - for each addition of a new constraint, a new constraint system is created.
     - this new constraint system has new degrees-of-freedom ( these degrees of freedom can be changed without violating the constraints already added. )

This should hopefully result, in a system whereby the constraints problem can be solved through a series single equation problems.

X - placement variables
Y - degrees of freedom, where Y is a subspace of X, which can altered without violating the constraints already added to the system.

'''

from assembly2lib import debugPrint
from lib3D import *
import numpy
from numpy import pi, inf
from numpy.linalg import norm
from solverLib import *

class ConstraintSystemPrototype:
    label = '' #over-ride in inheritence
    solveConstraintEq_tol = 10**-9
    def __init__(self, variableManager, parentSystem, obj1Name, obj2Name, feature1, feature2, constraintValue, featureType='plane' ):
        self.variableManager = variableManager
        self.parentSystem = parentSystem
        self.obj1Name = obj1Name
        self.obj2Name = obj2Name
        self.feature1 = feature1
        self.feature2 = feature2
        self.constraintValue = constraintValue
        self.featureType = featureType
        #self.X = variableManager.X0*0
        doc = variableManager.doc
        assert parentSystem.containtsObject( obj1Name ) or parentSystem.containtsObject( obj2Name )
        sys2ObjName = None
        if not parentSystem.containtsObject( obj1Name ):
            sys2ObjName = obj1Name
        if not parentSystem.containtsObject( obj2Name ):
            sys2ObjName = obj2Name
        if sys2ObjName <> None:
            if getattr( doc.getObject( sys2ObjName  ), 'fixedPosition', False ):
                self.sys2 = FixedObjectSystem( variableManager, sys2ObjName )
            else:
                self.sys2 = FreeObjectSystem( variableManager, sys2ObjName )
        else:
            self.sys2 = EmptySystem()
        debugPrint(4, '%s - sys2 %s' % (self.label, self.sys2.str() ) )
        self.init2()
        self.solveConstraintEq()       
        
    def init2(self):
        pass

    def containtsObject( self, objName ):
        debugPrint(4,  '%s locally contraints %s and %s' % (self.str(), self.obj1Name, self.obj2Name ))
        if self.obj1Name == objName:
            return True
        elif self.obj2Name == objName:
            return True
        return self.parentSystem.containtsObject( objName )

    def solveConstraintEq( self, solve_via_newton=True ):
        X0 = self.getX()
        tol = self.solveConstraintEq_tol
        if abs( self.constraintEq_value( X0 ) ) < tol: #constraint equation already satisfied.
            self.X = X0
        else:
            self.solveConstraintEq_dofs = [ d for d in self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom if not d.assignedValue ]
            if len(self.solveConstraintEq_dofs) > 0:
                Y0 =      [ d.value for d in self.solveConstraintEq_dofs ]
                maxStep = [ d.maxStep() for d in self.solveConstraintEq_dofs ]
                debugPrint(4, '%s: solveConstraintEq maxStep %s' % (self.str(),str(maxStep)))
                if solve_via_newton:
                    yOpt = solve_via_Newtons_method( self.constraintEq_f, Y0, maxStep, f_tol=tol, x_tol=0, maxIt=100, randomPertubationCount=2,
                                                     lineSearchIt=4, lineSearchIt_x0=20,
                                                     debugPrintLevel=debugPrint.level-2, printF= lambda txt: debugPrint(2, txt ))
                    self.X = self.constraintEq_setY(yOpt)
                else:
                    algName, warningMsg, optResults = solve_via_slsqp(self.constraintEq_f, Y0, fprime = None, f_tol=tol)
                    debugPrint(4, 'solver info: %s, %s, %s' % ( algName, warningMsg, optResults ))
                    self.X = self.constraintEq_setY( optResults['xOpt'] )
            if not abs( self.constraintEq_value(self.X) ) < tol:
                raise ValueError,"%s abs( self.constraintEq_value(self.X) ) > tol [%e > %e]. Constraint Tree:\n%s" % (self.str(), abs( self.constraintEq_value(self.X) ), tol, self.strSystemTree())
            for d in self.solveConstraintEq_dofs:
                d.assignedValue = False #cleaning up for future use
        if not hasattr( self, 'degreesOfFreedom' ):
            self.generateDegreesOfFreedom( )
        else:
            self.updateDegreesOfFreedom( )

    def constraintEq_setY(self, Y):
        for d,y in zip( self.solveConstraintEq_dofs, Y):
            d.setValue(y)
        self.parentSystem.update()
        self.sys2.update()
        return self.getX()
    def getX( self ):
        X_base = self.parentSystem.X + self.sys2.X
        X_base = X_base + sum([ d.X_contribution(X_base) for d in self.parentSystem.degreesOfFreedom if d.system == self.parentSystem ])
        X_base = X_base + sum([ d.X_contribution(X_base) for d in self.sys2.degreesOfFreedom if d.system == self.sys2 ]) 
        # if d.system <> self.sys2/parentSystem then d.X_contribution already been applied further up constraint system tree
        return X_base
    def getX2( self ):
        'like getX expect the contribution of self.degrees of freedom  is also done. Used for animate degrees of freedom.'
        X_base = self.getX()
        X = X_base + sum([ d.X_contribution(X_base) for d in self.degreesOfFreedom if d.system == self ]) 
        return X

    def update(self):
        if self.parentSystem <> None:
            self.parentSystem.update()
        self.solveConstraintEq()  

    def constraintEq_f( self, Y ):
        X = self.constraintEq_setY(Y)
        f_X = self.constraintEq_value(X)
        debugPrint(5, 'constraintEq_f, X %s, f(X) %s' % (X,f_X))
        return f_X
    def constraintEq_value( self, X ):
        raise ValueError, 'ConstraintSystemPrototype not supposed to be called directly'

    def generateDegreesOfFreedom( self ):
        raise ValueError, 'ConstraintSystemPrototype not supposed to be called directly'

    def updateDegreesOfFreedom( self ):
        raise ValueError, 'ConstraintSystemPrototype not supposed to be called directly'                    

    def getPos(self, objName, featureInd):
        obj =  self.variableManager.doc.getObject( objName )
        if self.featureType == 'plane':
            return obj.Shape.Faces[featureInd].Surface.Position
        elif self.featureType == 'cylinder':
            return obj.Shape.Faces[featureInd].Surface.Center
        elif self.featureType == 'circle':
            return obj.Shape.Edges[featureInd].Curve.Center
        else:
            raise NotImplementedError,"%s not programmed in yet" % self.featureType

    def getAxis(self, objName, featureInd):
        obj =  self.variableManager.doc.getObject( objName )
        if self.featureType == 'plane' or self.featureType == 'cylinder':
            return obj.Shape.Faces[featureInd].Surface.Axis
        elif self.featureType == 'circle':
            return obj.Shape.Edges[featureInd].Curve.Axis
        else:
            raise NotImplementedError,"%s not programmed in yet" % self.featureType


    def str(self, indent='', addDOFs=False):
        txt = '%s<%s System %s:%s-%s:%s heirachy %i>' % (indent, self.label, self.obj1Name, self.feature1, self.obj2Name, self.feature2, self.numberOfParentSystems())
        if addDOFs and hasattr( self, 'degreesOfFreedom'):
            txt = txt + ' %i degrees of freedom:' % len(self.degreesOfFreedom)
            txt = txt + ''.join( [ '\n%s%s' %(indent, d.str('  ')) for d in  self.degreesOfFreedom ] )
        return txt

    def numberOfParentSystems(self):
        count = 0
        sys = self
        while sys.parentSystem <> None:
            sys = sys.parentSystem
            count = count + 1
        return count

    def strSystemTree(self, dofs=True):
        txt = self.str(addDOFs=dofs)
        sys = self
        indent = ''
        while sys.parentSystem <> None:
            indent = indent+' '*4 if dofs else indent+' '*2
            if not isinstance(sys.sys2, EmptySystem):
                txt = txt + '\n' + sys.sys2.str(indent, addDOFs=dofs)
            txt = txt + '\n' + sys.parentSystem.str(indent, addDOFs=dofs)
            sys = sys.parentSystem
        return txt
        


class FixedObjectSystem(ConstraintSystemPrototype):
    def __init__(self, variableManager, objName):
        self.variableManager = variableManager
        self.objName = objName
        self.X = variableManager.objectsXComponent(objName, variableManager.X0)
        self.degreesOfFreedom = []
        self.parentSystem = None
    def containtsObject(self, objName):
        return self.objName == objName
    def solveConstraintEq( self ):
        pass
    def update(self):
        pass
    def str(self, indent='', addDOFs=False):
        return '%s<FixedObjectSystem %s> %s' % (indent, self.objName, '0 degrees of freedom' if addDOFs else '')

class EmptySystem( FixedObjectSystem ):
    def __init__(self ):
        self.X = 0
        self.degreesOfFreedom = []
    def containtsObject(self, objName):
        return False
    def str(self, indent=''):
        return '%s<EmptySystem>' % (indent)   

class FreeObjectSystem( FixedObjectSystem ):
    def __init__(self, variableManager, objName):
        self.objName = objName
        self.X = variableManager.X0*0
        i = variableManager.index[objName]
        self.degreesOfFreedom = [ PlacementDegreeOfFreedom( self, objName, len(self.X), i+j, variableManager.X0[i+j] ) for j in range(6) ]
    def str(self, indent='', addDOFs=False):
        txt = '%s<FreeObjectSystem %s>' % (indent, self.objName)
        if addDOFs:
            txt = txt + ' %i degrees of freedom:' % len(self.degreesOfFreedom)
            txt = txt + ''.join( [ '\n%s%s' %(indent, d.str('  ')) for d in  self.degreesOfFreedom ] )
        return txt

maxStep_linearDisplacement = 10
class PlacementDegreeOfFreedom:
    def __init__(self, parentSystem, objName, lenX, ind, initialValue):
        self.system = parentSystem
        self.objName = objName
        self.lenX = lenX
        self.ind = ind
        self.value = initialValue
        self.assignedValue = False
    def setValue( self, x):
        self.value = x
        self.assignedValue = True
    def X_contribution( self, X_system ):
        X = numpy.zeros(self.lenX)
        X[self.ind] = self.value
        return X
    def maxStep(self):
        if self.ind % 6 < 3:
            return maxStep_linearDisplacement
        else:
            return pi/5
    def rotational(self):
        return self.ind % 6 > 2
    def str(self, indent=''):
        return '%s<Placement DegreeOfFreedom %s-%s value:%f>' % (indent, self.objName, ['x','y','z','theta','phi','psi'][self.ind % 6], self.value)
    def __repr__(self):
        return self.str()

class AxisAlignmentUnion(ConstraintSystemPrototype):
    label = 'AxisAlignmentUnion'
    solveConstraintEq_tol = 10**-12

    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.a1_r = vM.rotateUndo( self.obj1Name, self.getAxis(self.obj1Name, self.feature1), vM.X0 )
        self.a2_r = vM.rotateUndo( self.obj2Name, self.getAxis(self.obj2Name, self.feature2), vM.X0 )

    def constraintEq_value( self, X ):
        vM = self.variableManager
        a = vM.rotate( self.obj1Name, self.a1_r, X )
        b = vM.rotate( self.obj2Name, self.a2_r, X )
        ax_prod = numpy.dot( a,b )
        directionConstraintFlag = self.constraintValue
        if directionConstraintFlag == "none" : 
            return (1 - abs(ax_prod))
        elif directionConstraintFlag == "aligned":
            return (1 - ax_prod)
        else:
            return (1 + ax_prod)

    def generateDegreesOfFreedom( self ):
        dofs = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        success = False
        #first try to look for an object which has 3 rotational degrees of freedom'
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in dofs if d.objName == objName and d.rotational() ]
            if len(matches) == 3:
                debugPrint(4, '%s Logic "%s": reducing from 3 to 1 rotational degree of freedom (2 rotation degrees fixed in defining axis of rotation)' % (self.label, objName))
                self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                self.degreesOfFreedom.append( AxisRotationDegreeOfFreedom( self, objName, self.variableManager.index[objName]) )
                self.degreesOfFreedom_updateInd = len(self.degreesOfFreedom) -1
                success = True
                break
            elif len(matches) == 1 and isinstance(matches[0], AxisRotationDegreeOfFreedom):
                vM = self.variableManager
                a = vM.rotate( self.obj1Name, self.a1_r, self.X )
                if numpy.array_equal(a, matches[0].axis):
                    debugPrint(4, '%s Logic "%s": AxisRotationDegreeOfFreedom with same axis already exists not reducing dofs for part' % (self.label, objName))
                    self.degreesOfFreedom_updateInd = -1
                    self.degreesOfFreedom = dofs
                    success = True
                else:
                    debugPrint(4, '%s Logic "%s": 2 different rotation axis specified, therefore fixing rotation (0 rotational degrees of freedom)' % (self.label, objName))
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.degreesOfFreedom_updateInd = -1
                    success = True
                    break
            elif len(matches) == 0:
                debugPrint(4, '%s Logic "%s": no rotational degrees of freedom ignoring.' % (self.label, objName))
                self.degreesOfFreedom = dofs
                self.degreesOfFreedom_updateInd = -1
                success = True
        if not success:
            raise ValueError, 'Panic! %s.generateDegreesOfFreedom Logic not programmed for the reduction of degrees of freedom of:\n%s' % (self.label,'\n'.join(d.str('  ') for d in dofs ))
        self.updateDegreesOfFreedom()
        
    def updateDegreesOfFreedom( self ):
        if self.degreesOfFreedom_updateInd > -1:
            vM = self.variableManager
            a = vM.rotate( self.obj1Name, self.a1_r, self.X )
            self.degreesOfFreedom[ self.degreesOfFreedom_updateInd ].setAxis( self.X, a )
            
class AngleUnion(AxisAlignmentUnion):
    label = 'AngleUnion'
    def constraintEq_value( self, X ):
        vM = self.variableManager
        a = vM.rotate( self.obj1Name, self.a1_r, X )
        b = vM.rotate( self.obj2Name, self.a2_r, X )
        return self.constraintValue - numpy.dot( a,b )

class AxisRotationDegreeOfFreedom:
    '''
    calculate the euler angles, theta_new, phi_new and psi_new so that
    R( theta_new, phi_new_, psi_new ) = R(axis, value) * R(theta_old, phi_old, psi_old)
    '''
    def __init__(self, parentSystem, objName, objInd):
        self.system = parentSystem
        self.objName = objName
        self.objInd = objInd
        self.value = 0.0
        self.assignedValue = False
    def setAxis(self, X, axis):
        self.lenX = len(X)
        i = self.objInd
        self.R0 = euler_ZYX_rotation_matrix( X[i+3], X[i+4], X[i+5] )
        self.X0 = X[i+3:i+6]
        self.axis = axis
    def setValue( self, x):
        self.value = x
        self.assignedValue = True
    def X_contribution( self, X_system ):
        R_axis = axis_rotation_matrix( self.value, *self.axis)
        X_desired = rotation_matrix_to_euler_ZYX(  numpy.dot( R_axis, self.R0 ) )
        #X_desired = self.X0
        # X_desired = X_system + X (for rotations of interest)
        X = numpy.zeros(self.lenX)
        i = self.objInd
        X[i+3:i+6] = numpy.array(X_desired) - X_system[i+3:i+6]
        return X
    def maxStep(self):             
        return pi/5
    def rotational(self):
        return True
    def str(self, indent=''):
        return '%s<AxisRotation DegreeOfFreedom %s axis:%s value:%f>' % (indent, self.objName, self.axis, self.value)
    def __repr__(self):
        return self.str()

class PlaneOffsetUnion(ConstraintSystemPrototype):
    label = 'PlaneOffsetUnion'
    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.a1_r =   vM.rotateUndo( self.obj1Name, self.getAxis(self.obj1Name, self.feature1), vM.X0 )
        self.pos1_r = vM.rotateAndMoveUndo( self.obj1Name, self.getPos(self.obj1Name, self.feature1), vM.X0 )
        self.pos2_r = vM.rotateAndMoveUndo( self.obj2Name, self.getPos(self.obj2Name, self.feature2), vM.X0 )
        
    def constraintEq_value( self, X ):
        vM = self.variableManager
        a = vM.rotate( self.obj1Name, self.a1_r, X )
        pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, X )
        pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, X )
        dist = numpy.dot(a, pos1 - pos2) #distance between planes
        return dist - self.constraintValue

    def generateDegreesOfFreedom( self ):
        dofs = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        #first try to look for an object which has 3 linear motion degrees of freedom'
        success = False
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in dofs if d.objName == objName and not d.rotational() ]
            if len(matches) == 3:
                debugPrint(4, 'PlaneOffsetUnion Logic: %s - reducing linear displacement degrees of freedom from 3 to 2' % objName)
                self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName, self.variableManager.index[objName]) )
                self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName, self.variableManager.index[objName]) )
                self.dofs_removed = matches
                success = True
                break
            elif len(matches) == 2:
                vM = self.variableManager
                planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, self.X )
                c = crossProduct( matches[0].directionVector, matches[1].directionVector)
                planeNormalMatches = c/norm(c)
                if norm(planeNormalVector - planeNormalMatches) < 10 **-6: #then constraint redudant
                    debugPrint(4, 'PlaneOffsetUnion Logic: %s - plane constraint with normal already exist, not reducing dofs for part' % objName)
                    self.degreesOfFreedom =  dofs
                    self.dofs_removed = []
                    success = True
                else:
                    debugPrint(4, 'PlaneOffsetUnion Logic: %s - reducing linear displacement degrees of freedom from 2 to 1' % objName)
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName, self.variableManager.index[objName]) )
                    self.dofs_removed = matches
                    success = True
                    break
            elif len(matches) == 1: 
                vM = self.variableManager
                planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, self.X )
                if abs(numpy.dot( planeNormalVector, matches[0].directionVector)) < 10 **-6: #then constraint redudant
                    debugPrint(4, 'PlaneOffsetUnion Logic: %s - planeNormal constraint does not effect remaining dof -> no dof reduction.' % objName)
                    self.degreesOfFreedom =  dofs
                    self.dofs_removed = []
                    success = True
                else:
                    debugPrint(4, 'PlaneOffsetUnion Logic: %s - reducing linear displacement degrees of freedom from 1 to 0' % objName)
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.dofs_removed = matches
                    success = True
                    break
                
        if not success:
            raise NotImplementedError, 'Panic! PlaneOffsetUnion Logic not programmed for the reduction of degrees of freedom of:\n%s' % '\n'.join(d.str('  ') for d in dofs )
        self.updateDegreesOfFreedom()
        
    def updateDegreesOfFreedom( self ):
        vM = self.variableManager
        planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, self.X )
        if len(self.dofs_removed) == 3:
            planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, self.X )
            d1,d2 = plane_degrees_of_freedom(planeNormalVector)
            self.degreesOfFreedom[-2].setDirection(self.X, d1)
            self.degreesOfFreedom[-1].setDirection(self.X, d2)
        elif len(self.dofs_removed) == 2:
            c = crossProduct( self.dofs_removed[0].directionVector, self.dofs_removed[1].directionVector)
            planeNormalMatches = c/norm(c)
            d = planeIntersection( planeNormalVector, planeNormalMatches )
            self.degreesOfFreedom[-1].setDirection(self.X, d)
        elif len(self.dofs_removed) < 2: #then object fixed, or constraint redundant.
            pass
        else:
            raise NotImplemented

class LinearMotionDegreeOfFreedom:
    def __init__(self, parentSystem, objName, objInd):
        self.system = parentSystem
        self.objName = objName
        self.objInd = objInd
        self.value = 0.0
        self.assignedValue = False
    def setDirection(self, X, directionVector):
        self.lenX = len(X)
        self.directionVector = directionVector
    def setValue( self, x):
        self.value = x
        self.assignedValue = True
    def X_contribution( self, X_system ):
        X = numpy.zeros(self.lenX)
        i = self.objInd
        X[i:i+3] = self.directionVector*self.value
        return X
    def maxStep(self):             
        return maxStep_linearDisplacement #inf
    def rotational(self):
        return False
    def str(self, indent=''):
        return '%s<LinearMotion DegreeOfFreedom %s direction:%s value:%f>' % (indent, self.objName, self.directionVector, self.value)
    def __repr__(self):
        return self.str()

class AxisDistanceUnion(ConstraintSystemPrototype):
    label = 'AxisDistanceUnion'
    solveConstraintEq_tol = 10**-7
    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.a1_r =   vM.rotateUndo( self.obj1Name, self.getAxis(self.obj1Name, self.feature1), vM.X0 )
        self.a2_r =   vM.rotateUndo( self.obj2Name, self.getAxis(self.obj2Name, self.feature2), vM.X0 )
        self.pos1_r = vM.rotateAndMoveUndo( self.obj1Name, self.getPos(self.obj1Name, self.feature1), vM.X0 )
        self.pos2_r = vM.rotateAndMoveUndo( self.obj2Name, self.getPos(self.obj2Name, self.feature2), vM.X0 )

    def constraintEq_value( self, X ):
        vM = self.variableManager
        a1 = vM.rotate( self.obj1Name, self.a1_r, X )
        a2 = vM.rotate( self.obj2Name, self.a2_r, X )
        pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, X )
        pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, X )
        #dist = distance_between_axes( pos1, a1, pos2, a2 )
        dist = distance_between_two_axes_3_points( pos1, a1, pos2, a2 )
        return dist - self.constraintValue

    def generateDegreesOfFreedom( self ):
        dofs = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        #first try to look for an object which has 3 linear motion degrees of freedom'
        success = False
        if self.constraintValue <> 0:
            raise NotImplementedError, '%s self.constraintValue <> 0 not implemented yet' % self.label
        vM = self.variableManager
        axisVector = vM.rotate( self.obj1Name, self.a1_r, self.X )
        self.dof_added = False
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in dofs if d.objName == objName and not d.rotational() ]
            if len(matches) == 3:
                debugPrint(4, '%s Logic: %s - reducing linear displacement degrees of freedom from 3 to 1' % (self.label, objName))
                self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName, self.variableManager.index[objName]) )
                self.dof_added = True
                success = True
                break
            elif len(matches) == 2:
                c = crossProduct( matches[0].directionVector, matches[1].directionVector)
                planeNormalMatches = c/norm(c)
                if abs(numpy.dot( axisVector, planeNormalMatches)) < 10 **-6: #then co-planar
                    debugPrint(4, '%s Logic: %s axis in movement plane, therefore linear degrees of freedom reduced from 2 to 1' % (self.label, objName))
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName, self.variableManager.index[objName]) )
                    self.dof_added = True
                    success = True
                    break
                else:
                    debugPrint(4, '%s Logic: %s axis not in movement plane, therefore linear degrees of freedom reduced from 2 to 0' % (self.label, objName))
                    self.degreesOfFreedom =  [ d for d in dofs if not d in matches ]
                    success = True
                    break
            elif len(matches) == 1: 
                if abs(numpy.dot(axisVector , matches[0].directionVector)) < 10 **-6: #then constraint redudant
                    debugPrint(4, '%s Logic: %s - axis movement constraint does not effect remaining dof -> no dof reduction.' % (self.label, objName))
                    self.degreesOfFreedom =  dofs
                    success = True
                else:
                    debugPrint(4, '%s Logic: %s - axis movement constraint different from last linear displacement degree of freedom -> reducing degrees of freedom from 1 to 0' % (self.label, objName))
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    success = True
                    break
                
        if not success:
            raise ValueError, 'Panic! PlaneOffsetUnion Logic not programmed for the reduction of degrees of freedom of:\n%s' % '\n'.join(d.str('  ') for d in dofs )
        self.updateDegreesOfFreedom()
        
    def updateDegreesOfFreedom( self ):
        if self.dof_added:
            vM = self.variableManager
            axisVector = vM.rotate( self.obj1Name, self.a1_r, self.X )
            self.degreesOfFreedom[-1].setDirection(self.X, axisVector)
