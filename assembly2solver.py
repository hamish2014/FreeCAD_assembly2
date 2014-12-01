'''
library for solving assembly 2 constraints
'''


from assembly2lib import *
from assembly2lib import __dir__ #variables not imported with * directive ...
from lib3D import *
import numpy
from numpy import pi, inf
import scipy.optimize
from axialConstraint import AxialConstraint
from planeConstraint import PlaneConstraint
from circularEdgeConstraint import CircularEdgeConstraint

class VariableManager:
    def __init__(self, doc):
        self.doc = doc
        self.placementVariables = {}
    def getPlacementValues(self, objectName):
        if not self.placementVariables.has_key(objectName):
            self.placementVariables[objectName] = PlacementVariables( self.doc, objectName )
        return self.placementVariables[objectName]
    def getValues(self):
        return sum([ pV.getValues() for key,pV in self.placementVariables.iteritems() if not pV.fixed ], [])
    def setValues(self, values):
        i = 0
        for key,pV in self.placementVariables.iteritems():
            if not pV.fixed:
                pV.setValues( values[ i*6: (i+1)*6 ] )
                i = i + 1
    def updateFreeCADValues(self):
        [ pV.updateFreeCADValues() for pV in self.placementVariables.values() if not pV.fixed ]
    def bounds(self):
        bounds = []
        for key,pV in self.placementVariables.iteritems():
            if not pV.fixed:
                bounds = bounds + pV.bounds()
        return bounds
    def peturbValues(self, objectsToPeturb):
        X = []
        for key,pV in self.placementVariables.iteritems():
            if not pV.fixed:
                y = numpy.array( pV.getValues() )
                if key in objectsToPeturb:
                    y[0:3] = y[0:3] + 42*( numpy.random.rand(3) - 0.5 )
                    y[3:6] = 2*pi *( numpy.random.rand(3) - 0.5 )
                X = X + y.tolist()
        return X
    def fixObj( self, objectName ):
        self.placementVariables[objectName].fixed = True
    def fixEveryObjectExcept(self, objectName):
        for key,pV in self.placementVariables.iteritems():
            if key <> objectName:
                pV.fixed = True
    def objFixed( self, objectName ):
        return self.placementVariables[objectName].fixed 


class PlacementVariables:
    def __init__(self, doc, objName):
        '''
        variables
        - x, y, z
        - theta, phi, psi  #using euler angles instead of quaternions because i think it will make the constraint problem easier to solver...

        NB - object,shapes,faces placement properties given in abosolute co-ordinates
        >>> App.ActiveDocument.Pocket.Placement
        Placement [Pos=(0,0,0), Yaw-Pitch-Roll=(0,0,0)]
        >>> Pocket.Shape.Faces[9].Surface.Center
        Vector (25.0, 15.0, 100.0)
        >>> Pocket.Placement.Base.x = 10
        >>> Pocket.Shape.Faces[9].Surface.Center
        Vector (35.0, 15.0, 100.0)
        >>> Pocket.Shape.Faces[9].Surface.Axis
        Vector (0.0, 0.0, 1.0)
        >>> Pocket.Placement.Rotation.Q = ( 1, 0, 0, 0) #rotate 180 about the x-axis
        >>> Pocket.Shape.Faces[9].Surface.Axis
        Vector (0.0, 0.0, -1.0)
        >>> Pocket.Shape.Faces[9].Surface.Center
        Vector (35.0, -15.0, -100.0)

        '''
        self.doc = doc
        self.objName = objName
        obj = doc.getObject(self.objName)
        self.x = obj.Placement.Base.x
        self.y = obj.Placement.Base.y
        self.z = obj.Placement.Base.z
        self.theta, self.phi, self.psi  = quaternion_to_euler( *obj.Placement.Rotation.Q )
        self.fixed = obj.fixedPosition

    def getValues(self):
        assert not self.fixed
        return [self.x, self.y, self.z, self.theta, self.phi, self.psi]

    def bounds(self):
        return [ [ -inf, inf], [ -inf, inf], [ -inf, inf], [-pi,pi], [-pi,pi], [-pi,pi] ]

    def setValues(self, values):
        assert not self.fixed
        self.x, self.y, self.z, self.theta, self.phi, self.psi = values

    def updateFreeCADValues(self):
        '''http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions '''        
        assert not self.fixed
        Placement = self.doc.getObject(self.objName).Placement
        Placement.Base.x = self.x
        Placement.Base.y = self.y
        Placement.Base.z = self.z
        Placement.Rotation.Q = euler_to_quaternion( self.theta, self.phi, self.psi )
        self.doc.getObject(self.objName).touch()
    
    def rotate( self, p):
        #debugPrint( 3, "p %s" % p)
        #debugPrint( 3, "theta %2.1f, phi %2.1f, psi %2.1f" % ( self.theta/pi*180, self.phi/pi*180, self.psi/pi*180 ))
        #debugPrint( 3, 'result %s' % euler_ZYX_rotation( p, self.theta, self.phi, self.psi ))
        return euler_ZYX_rotation( p, self.theta, self.phi, self.psi )

    def rotate_undo( self, p ): # or unrotate
        R = euler_ZYX_rotation_matrix( self.theta, self.phi, self.psi )
        return numpy.linalg.solve(R,p)

    def rotate_and_then_move( self, p):
        return self.rotate(p) + numpy.array([ self.x, self.y, self.z ])

    def rotate_and_then_move_undo( self, p): # or un(rotate_and_then_move)
        return self.rotate_undo( numpy.array(p) - numpy.array([ self.x, self.y, self.z ]) )        


def solve_via_simplex( constraintEqs, x0, bounds ):
    algName = 'scipy.optimize.fmin (simplex, nelder mead solver)'
    errorNorm = lambda x: numpy.linalg.norm(constraintEqs(x))
    R = scipy.optimize.fmin( errorNorm, x0, disp=False, full_output=True)
    optResults = dict( zip(['xOpt', 'fOpt' , 'iter', 'funCalls', 'warnInt'], R ) ) # see scipy.optimize.fmin_bfgs docs for info
    if optResults['warnInt'] == 0:
        warningMsg = ''
    else:
        warningMsg = { 1: 'Maximum number of function evaluations made.',
                       2: 'Maximum number of iterations reached.' }[optResults['warnInt']]   
    return algName, warningMsg, optResults

def solve_via_bfgs( constraintEqs, x0, bounds ):
    algName = 'scipy.optimize.fmin_bfgs'
    errorNorm = lambda x: numpy.linalg.norm(constraintEqs(x))
    R = scipy.optimize.fmin_bfgs( errorNorm, x0 , disp=False, full_output=True)
    optResults = dict( zip(['xOpt', 'fOpt' , 'gOpt', 'BOpt', 'func_calls', 'grad_calls', 'warnInt'], R ) ) # see scipy.optimize.fmin_bfgs docs for info
    if optResults['warnInt'] == 0:
        warningMsg = ''
    else:
        warningMsg = { 1: 'Maximum number of iterations exceeded.',
                       2: 'Gradient and/or function calls not changing.' }[optResults['warnInt']]
    return algName, warningMsg, optResults

def solve_via_slsqp( constraintEqs, x0, bounds , iterations=160 ):
    algName = 'scipy.optimize.fmin_slsqp (Sequential Least SQuares Programming)'
    errorNorm = lambda x: numpy.linalg.norm(constraintEqs(x))
    R = scipy.optimize.fmin_slsqp( errorNorm, x0, bounds=bounds, disp=False, full_output=True, iter=iterations)
    optResults = dict( zip(['xOpt', 'fOpt' , 'iter', 'imode', 'smode'], R ) ) # see scipy.optimize.fmin_bfgs docs for info
    if optResults['imode'] == 0:
        warningMsg = ''
    else:
        warningMsg = optResults['smode']
    return algName, warningMsg, optResults

#def solve_via_fsolve( constraintEqs, x0, bounds ): 
#    Does not work as number of constraint equations does not equal number of variables.
#    algName = 'scipy.optimize.fsolve'
#    xOpt, infodict , solvedInt, warningMsg = scipy.optimize.fsolve( constraintEqs, x0, full_output=False)
#    infodict['xOpt'] = xOpt
#    return algName, warningMsg, infodict

def objects_violating_constraints( constraints ):
    violatedConstraints = [c for c in constraints if not c.satisfied() ]
    vNames = [ vc.constraintObj.Name for vc in violatedConstraints ]
    debugPrint( 3, "violated constraints: " + ', '.join(vNames) )
    vObjects = sum( [ vc.objectNames() for vc in violatedConstraints ], [] )
    debugPrint( 3, "objects associated to these constraints: " + ', '.join( list(set(vObjects))))
    return vObjects


def solveConstraints( doc, solver=solve_via_slsqp, random_restart_attempts = 6  ):
    '''
    - gernerate a list of variables
    - for each constraint, parse varialbe as to generate constraint error equations.
    - use numpy non-linear solver to solve equations as to minize error.
    '''

    variableManager = VariableManager( doc )
    constraints = []
    mapper = { 
        'axial':AxialConstraint, 
        'plane':PlaneConstraint, 
        'circularEdge':CircularEdgeConstraint
        }
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            debugPrint(3, "assembly2solver parsing %s" % obj.Name )
            constraints.append( mapper[obj.Type]( doc, obj, variableManager) )

    violatedConstraints = [c for c in constraints if not c.satisfied() ]
    vNames = [ vc.constraintObj.Name for vc in violatedConstraints ]
    debugPrint( 3, "violated constraints: " + ', '.join(vNames) )
    vObjects = sum( [ vc.objectNames() for vc in violatedConstraints ], [] )
    debugPrint( 3, "objects associated to these constraints: " + ', '.join( list(set(vObjects))))
    vObjects_connectivety = [ sum( obj in c.objectNames() for c in constraints ) for obj in vObjects ]
    debugPrint( 3, "repective connectivety %s " %  vObjects_connectivety)
    if len(violatedConstraints) == 1 and len(vObjects_connectivety) == 2 and sum(vObjects_connectivety) > 2:
        if not variableManager.objFixed(vObjects[0]) and not variableManager.objFixed(vObjects[1]):
            for obj, conn in zip(vObjects, vObjects_connectivety):
                if conn == 1: # makes vObjects_connectivety[0] == 1 or vObjects_connectivety[1] == 1 unnessary
                    variableManager.fixEveryObjectExcept( obj )
                    debugPrint( 3, "moving %s as to satisfy %s, everything else fixed" % ( obj, vNames[0]) )
                    constraints = violatedConstraints
    
    def constraintEqs(x): #equations which need to solved inorder to assemble parts
        variableManager.setValues(x)
        errors = sum( [c.errors() for c in constraints], [] )
        debugPrint( 4, "constraint errors %s" % errors )
        return errors

    x0 = variableManager.getValues()
    debugPrint(3, "variableManager.getValues() %s" % x0)

    algName, warningMsg, optResults = solver(constraintEqs, x0, variableManager.bounds() )
    debugPrint(3, str(optResults))
    if warningMsg <>  '' or optResults['fOpt'] > 10**-4 and random_restart_attempts > 0:
        for i in range(random_restart_attempts):
            variableManager.setValues(x0)
            xN = variableManager.peturbValues( vObjects )
            algName, warningMsg, optResults = solver(constraintEqs, xN, variableManager.bounds() )
            debugPrint(3, str(optResults))
            if warningMsg == '' and optResults['fOpt'] < 10**-4:
                break
    

    if warningMsg == '' and optResults['fOpt'] < 10**-4: #then constraints satisfied
        variableManager.setValues( optResults['xOpt'] )
        variableManager.updateFreeCADValues( )
    else:
        FreeCAD.Console.PrintError("UNABLE TO SOLVE ASSEMBLY CONSTRAINTS. Info:\n")
        FreeCAD.Console.PrintError("  optimization algorithm could not minimize the norm of constraint errors\n" )
        FreeCAD.Console.PrintError("    optimization algorithm used  : %s\n" % algName )
        FreeCAD.Console.PrintError("    optimization warning message : %s\n" %  warningMsg)
        for k,v in optResults.iteritems():
            FreeCAD.Console.PrintError("    %s: %s\n" % (k,v))
        FreeCAD.Console.PrintError("UNABLE TO SOLVE ASSEMBLY CONSTRAINTS. refer to the Report View window for info\n")
        # http://www.blog.pythonlibrary.org/2013/04/16/pyside-standard-dialogs-and-message-boxes/
        flags = QtGui.QMessageBox.StandardButton.Yes 
        flags |= QtGui.QMessageBox.StandardButton.No
        message = """The assembly 2 solver failed to find a solution to the specified constraints.
This is due to either
  - the contraint problem being too difficult for the solver, or
  - impossible/contridictorary constraints have be specified.

Either way, the solution is most likely to delete the problematic constraints, and try again using a different constraint scheme.
Delete constraints [%s]?
 """ % ', '.join(vNames)
        response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Solver Failure!",
                                              message,
                                              flags)
        if response == QtGui.QMessageBox.Yes:
            for name in vNames:
                doc.removeObject(name)
                FreeCAD.Console.PrintError("removed constraint %s" % name)
        
    #print(xOpt)


class Assembly2SolveConstraintsCommand:
    def Activated(self):
        solveConstraints( FreeCAD.ActiveDocument )
    def GetResources(self): 
        return {
            'Pixmap' : os.path.join( __dir__ , 'assembly2SolveConstraints.svg' ) , 
            'MenuText': 'Solve Assembly 2 constraints', 
            'ToolTip': 'Solve Assembly 2 constraints'
            } 

FreeCADGui.addCommand('assembly2SolveConstraints', Assembly2SolveConstraintsCommand())

