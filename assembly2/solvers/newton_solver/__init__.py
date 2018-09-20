'''
Newton solver from commit d084cd00d9e9d884002527ef581d957d94433647
Date:   Thu Dec 11 09:06:24 2014
'''

import traceback, time
import FreeCAD
from assembly2.solvers.common import *
from assembly2.core import QtGui
from variableManager import VariableManager
from constraints import AxialConstraint, PlaneConstraint, CircularEdgeConstraint, AngleConstraint, SphericalSurfaceConstraint
import numpy


def solve_via_simplex( constraintEqs, x0, bounds ):
    import scipy.optimize
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
    import scipy.optimize
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
    import scipy.optimize
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
#    import scipy
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



def solveConstraints(
        doc,
        showFailureErrorDialog=True,
        printErrors=True,
        use_cache=False,
        solver=solve_via_slsqp,
        random_restart_attempts=1
):
    assert not use_cache, "cache not implemented for Newton solver"
    T_start = time.time()
    variableManager = VariableManager( doc )
    constraints = []
    mapper = { 
        'axial':AxialConstraint, 
        'plane':PlaneConstraint, 
        'circularEdge':CircularEdgeConstraint,
        'angle_between_planes':AngleConstraint,
        'sphericalSurface':SphericalSurfaceConstraint
        }
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            debugPrint(3, "assembly2solver parsing %s" % obj.Name )
            #try:
            constraints.append( mapper[obj.Type]( doc, obj, variableManager) )
            #except AttributeError, msg:
            #    if str(msg).strip() == "'NoneType' object has no attribute 'Placement'":
            #        flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.Abort
            #        message = "%s is refering to an object no longer in the assembly. Delete constraint? otherwise abort solving." % obj.Name
            #        response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Broken Constraint", message, flags )
            #        if response == QtGui.QMessageBox.Yes:
            #            FreeCAD.Console.PrintError("removing constraint %s" % obj.Name)
            #            doc.removeObject(obj.Name)
            #        else:
            #            FreeCAD.Console.PrintError("aborted solving constraints due to %s refering a non-existent object" % obj.Name)
            #            return
            #    else:
            #        raise AttributeError(msg)

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
        return  optResults['xOpt']
    elif showFailureErrorDialog and QtGui.qApp != None:
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
        message = """The Assembly 2 Netwon solver failed to find a solution to the specified constraints.
This is due to either
  - the contraint problem being too difficult for the solver, or
  - impossible/contridictorary constraints have be specified.

Either way, the solution is most likely to delete the problematic constraints, and try again using a different constraint scheme.
Delete constraints [%s]?
 """ % ', '.join(vNames)
        response = QtGui.QMessageBox.critical(
            QtGui.qApp.activeWindow(),
            "Solver Failure!",
            message,
            flags
        )
        if response == QtGui.QMessageBox.Yes:
            for name in vNames:
                doc.removeObject(name)
                FreeCAD.Console.PrintError("removed constraint %s" % name)
        return None
