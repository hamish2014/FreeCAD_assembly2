'''
library for solving assembly 2 constraints

Notes regarding the assembly constraints problem.
  1. majority of assembly constraints can be solved by only moving one part

Approach followed is therefore, for the case of adding a constraint
  1. first try solve problem by moving&rotating one part only, if this fails then
  2. solve entire constraint system by moving&rotating all non-fixed objects 

'''

if __name__ == '__main__': #then testing library.
    import sys
    sys.path.append('/usr/lib/freecad/lib/') #path to FreeCAD library on Linux
    import FreeCADGui
    assert not hasattr(FreeCADGui, 'addCommand')
    FreeCADGui.addCommand = lambda x,y: 0

from assembly2lib import *
from lib3D import *
import time, numpy
from numpy import pi, inf
from numpy.linalg import norm
from solverLib import *
from variableManager import VariableManager
from constraintSystems import *
import traceback

def constraintsObjectsAllExist( doc ):
    objectNames = [ obj.Name for obj in doc.Objects if not 'ConstraintInfo' in obj.Content ]
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            if not (obj.Object1 in objectNames and obj.Object2 in objectNames):
                flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.Abort
                message = "%s is refering to an object no longer in the assembly. Delete constraint? otherwise abort solving." % obj.Name
                response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Broken Constraint", message, flags )
                if response == QtGui.QMessageBox.Yes:
                    FreeCAD.Console.PrintError("removing constraint %s" % obj.Name)
                    doc.removeObject(obj.Name)
                else:
                    missingObject = obj.Object2 if obj.Object1 in objectNames else obj.Object1
                    FreeCAD.Console.PrintError("aborted solving constraints due to %s refering the non-existent object %s" % (obj.Name, missingObject))
                    return False            
    return True
    
def findBaseObject( doc, objectNames  ):
    debugPrint( 4,'solveConstraints: searching for fixed object to begin solving constraints from.' )
    fixed = [ getattr( doc.getObject( name ), 'fixedPosition', False ) for name in objectNames ]
    if sum(fixed) > 0:
        return objectNames[ fixed.index(True) ]        
    if sum(fixed) == 0:
        debugPrint( 1, 'It is recommended that the assembly 2 module is used with parts imported using the assembly 2 module.')
        debugPrint( 1, 'This allows for part updating, parts list support, object copying (shift + assembly2 move) and also tells the solver which objects to treat as fixed.')
        debugPrint( 1, 'since no objects have the fixedPosition attribute, fixing the postion of the first object in the first constraint')
        debugPrint( 1, 'assembly 2 solver: assigning %s a fixed position' % objectNames[0])
        return objectNames[0]

def solveConstraints( doc, showFailureErrorDialog=True, printErrors=True ):
    if not constraintsObjectsAllExist(doc):
        return
    T_start = time.time()
    updateOldStyleConstraintProperties(doc)
    constraintObjectQue = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content ]
    #doc.Objects already in tree order so no additional sorting / order checking required for constraints.
    objectNames = []
    for c in constraintObjectQue:
        for attr in ['Object1','Object2']:
            objectName = getattr(c, attr, None)
            if objectName <> None and not objectName in objectNames:
                objectNames.append( objectName )
    variableManager = VariableManager( doc, objectNames )
    debugPrint(3,' variableManager.X0 %s' % variableManager.X0 )
    constraintSystem = FixedObjectSystem( variableManager, findBaseObject(doc, objectNames) )
    debugPrint(4, 'solveConstraints base system: %s' % constraintSystem.str() )
    

    solved = True
    for constraintObj in constraintObjectQue:
        debugPrint( 3, '  parsing %s, type:%s' % (constraintObj.Name, constraintObj.Type ))
        try:
            cArgs = [variableManager, constraintObj]
            if not constraintSystem.containtsObject( constraintObj.Object1) and not constraintSystem.containtsObject( constraintObj.Object2):
                constraintSystem = AddFreeObjectsUnion(constraintSystem, *cArgs)
            if constraintObj.Type == 'plane':
                if constraintObj.SubElement2.startswith('Face'): #otherwise vertext
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
                raise NotImplementedError, 'constraintType %s not supported yet' % constraintObj.Type
        except Assembly2SolverError, msg:
            if printErrors:
                FreeCAD.Console.PrintError('UNABLE TO SOLVE CONSTRAINTS! info:')
                FreeCAD.Console.PrintError(msg)
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
        variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
        debugPrint(2,'Constraint system solved in %2.2fs; resulting system has %i degrees-of-freedom' % (time.time()-T_start, len( constraintSystem.degreesOfFreedom)))
    elif showFailureErrorDialog and  QtGui.qApp <> None: #i.e. GUI active
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
        response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Solver Failure!", message, flags)
        if response == QtGui.QMessageBox.Yes:
            name = constraintObj.Name
            doc.removeObject( name )
            FreeCAD.Console.PrintError("removed constraint %s" % name )
        #elif response == QtGui.QMessageBox.Ignore:
        #    variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
    return constraintSystem if solved else None

class Assembly2SolveConstraintsCommand:
    def Activated(self):
        solveConstraints( FreeCAD.ActiveDocument )
    def GetResources(self): 
        return {
            'Pixmap' : ':/assembly2/icons/assembly2SolveConstraints.svg', 
            'MenuText': 'Solve Assembly 2 constraints', 
            'ToolTip': 'Solve Assembly 2 constraints'
            } 

FreeCADGui.addCommand('assembly2SolveConstraints', Assembly2SolveConstraintsCommand())






if __name__ == '__main__':
    import glob, argparse, time
    print('Testing assembly 2 solver on assemblies under tests/')
    parser = argparse.ArgumentParser(description="Test assembly 2 solver.")
    parser.add_argument('--lastTestCaseOnly', action='store_true')
    args = parser.parse_args()

    debugPrint.level = 4
    t_start = time.time()
    testFiles = sorted(glob.glob('tests/*.fcstd')) 
    if args.lastTestCaseOnly:
        testFiles = testFiles[-1:]
    for testFile in testFiles:
        print(testFile)
        doc =  FreeCAD.open(testFile)
        constraintSystem = solveConstraints( doc )
        if constraintSystem == None:
            print('Failed on %s' % testFile)
            exit()
        print('\n\n\n')
    print('All %i tests passed, time taken %3.2fs' % (len(testFiles), time.time() - t_start))
