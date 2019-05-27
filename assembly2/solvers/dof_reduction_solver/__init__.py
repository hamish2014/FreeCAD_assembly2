'''
degree-of-freedom reduction solver
'''
from assembly2.lib3D import *
from assembly2.solvers.common import *
from assembly2.core import QtGui
import time, numpy
from numpy import pi, inf
from numpy.linalg import norm
from .solverLib import *
from .variableManager import VariableManager
from .constraintSystems import *

import traceback
from . import cache as cacheLib

cache = cacheLib.defaultCache

def solveConstraints(
        doc,
        showFailureErrorDialog=True,
        printErrors=True,
        use_cache=False
):
    T_start = time.time()
    constraintObjectQue = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content ]
    #doc.Objects already in tree order so no additional sorting / order checking required for constraints.
    objectNames = []
    for c in constraintObjectQue:
        for attr in ['Object1','Object2']:
            objectName = getattr(c, attr, None)
            if objectName != None and not objectName in objectNames:
                objectNames.append( objectName )
    variableManager = VariableManager( doc, objectNames )
    debugPrint(3,' variableManager.X0 %s' % variableManager.X0 )
    constraintSystem = FixedObjectSystem( variableManager, findBaseObject(doc, objectNames) )
    debugPrint(4, 'solveConstraints base system: %s' % constraintSystem.str() )

    solved = True
    
    if use_cache:
        t_cache_start = time.time()
        constraintSystem, que_start = cache.retrieve( constraintSystem, constraintObjectQue)
        debugPrint(3,"~cached solution available for first %i out-off %i constraints (retrieved in %3.2fs)" % (que_start, len(constraintObjectQue), time.time() - t_cache_start ) )
        cache.prepare()
    else:
        que_start = 0

    for constraintObj in constraintObjectQue[que_start:]:
        debugPrint( 3, '  parsing %s, type:%s' % (constraintObj.Name, constraintObj.Type ))
        try:
            cArgs = [variableManager, constraintObj]
            if not constraintSystem.containtsObject( constraintObj.Object1) and not constraintSystem.containtsObject( constraintObj.Object2):
                constraintSystem = AddFreeObjectsUnion(constraintSystem, *cArgs)
            if constraintObj.Type == 'plane':
                if constraintObj.SubElement2.startswith('Face'): #otherwise vertex
                    constraintSystem = AxisAlignmentUnion(constraintSystem, *cArgs,  constraintValue = constraintObj.directionConstraint )
                constraintSystem = PlaneOffsetUnion(constraintSystem,  *cArgs, constraintValue = constraintObj.offset.Value)
            elif constraintObj.Type == 'angle_between_planes':
                constraintSystem = AngleUnion(constraintSystem,  *cArgs, constraintValue = constraintObj.angle.Value*pi/180 )
            elif constraintObj.Type == 'axial':
                constraintSystem = AxisAlignmentUnion(constraintSystem,  *cArgs, constraintValue = constraintObj.directionConstraint)
                constraintSystem =  AxisDistanceUnion(constraintSystem,  *cArgs, constraintValue = 0)
                if constraintObj.lockRotation: constraintSystem =  LockRelativeAxialRotationUnion(constraintSystem,  *cArgs, constraintValue = 0)
            elif constraintObj.Type == 'circularEdge':
                constraintSystem = AxisAlignmentUnion(constraintSystem,  *cArgs, constraintValue=constraintObj.directionConstraint)
                constraintSystem = AxisDistanceUnion(constraintSystem,  *cArgs, constraintValue=0)
                constraintSystem = PlaneOffsetUnion(constraintSystem,  *cArgs, constraintValue=constraintObj.offset.Value)
                if constraintObj.lockRotation: constraintSystem =  LockRelativeAxialRotationUnion(constraintSystem,  *cArgs, constraintValue = 0)
            elif constraintObj.Type == 'sphericalSurface':
                constraintSystem = VertexUnion(constraintSystem,  *cArgs, constraintValue=0)
            else:
                raise NotImplementedError('constraintType %s not supported yet' % constraintObj.Type)
            if use_cache:
                cache.record( constraintSystem )

                    
        except Assembly2SolverError as e:
            if printErrors:
                FreeCAD.Console.PrintError('UNABLE TO SOLVE CONSTRAINTS! info:')
                FreeCAD.Console.PrintError(e)
            solved = False
            break
        except:
            if printErrors:
                FreeCAD.Console.PrintError('UNABLE TO SOLVE CONSTRAINTS! info:')
                FreeCAD.Console.PrintError( traceback.format_exc())
            solved = False
            break
    if solved:
        debugPrint(4,'placement X %s' % constraintSystem.variableManager.X )

        if use_cache:
            t_cache_record_start = time.time()
            cache.commit( constraintSystem, constraintObjectQue, que_start)
            debugPrint( 4,'  time cache.record %3.2fs' % (time.time()-t_cache_record_start) )

        t_update_freecad_start = time.time()
        variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
        debugPrint( 4,'  time to update FreeCAD placement variables %3.2fs' % (time.time()-t_update_freecad_start) )

        debugPrint(2,'Constraint system solved in %2.2fs; resulting system has %i degrees-of-freedom' % (time.time()-T_start, len( constraintSystem.degreesOfFreedom)))
    elif showFailureErrorDialog and  QtGui.qApp != None: #i.e. GUI active
        # http://www.blog.pythonlibrary.org/2013/04/16/pyside-standard-dialogs-and-message-boxes/
        flags = QtGui.QMessageBox.StandardButton.Yes
        flags |= QtGui.QMessageBox.StandardButton.No
        #flags |= QtGui.QMessageBox.Ignore
        message = """The assembly2 solver failed to satisfy the constraint "%s".

possible causes
  - impossible/contridictorary constraints have be specified, or
  - the contraint problem is too difficult for the solver, or
  - a bug in the assembly 2 workbench

potential solutions
  - redefine the constraint (popup menu item in the treeView)
  - delete constraint, and try again using a different constraint scheme.

Delete constraint "%s"?
""" % (constraintObj.Name, constraintObj.Name)
        response = QtGui.QMessageBox.critical(QtGui.QApplication.activeWindow(), "Solver Failure!", message, flags)
        if response == QtGui.QMessageBox.Yes:
            from assembly2.constraints import removeConstraint
            removeConstraint( constraintObj )
        #elif response == QtGui.QMessageBox.Ignore:
        #    variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
    return constraintSystem if solved else None
