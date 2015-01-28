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
from assembly2lib import __dir__ #variables not imported with * directive ...
from lib3D import *
import numpy
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
    if sum(fixed) == 0:
        raise ValueError, "the constraint solver requires at least 1 object with fixedPosition=True inorder to solve the system"    
    return objectNames[ fixed.index(True) ]


def solveConstraints( doc ):
    if not constraintsObjectsAllExist(doc):
        return
    updateOldStyleConstraintProperties(doc)
    constraintObjectQue = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content ]
    #doc.Objects already in tree order so no additional sorting / order checking required for constraints.
    conObjects = sum( [[ c.Object1 ] for c in constraintObjectQue], [] ) + sum( [[ c.Object2 ] for c in constraintObjectQue], [] )
    objectNames = [ obj.Name for obj in doc.Objects if hasattr(obj,'Placement') and obj.Name in conObjects ]
    variableManager = VariableManager( doc, objectNames )
    debugPrint(3,' variableManager.X0 %s' % variableManager.X0 )
    constraintSystem = FixedObjectSystem( variableManager, findBaseObject(doc, objectNames) )
    debugPrint(4, 'solveConstraints base system: %s' % constraintSystem.str() )
    

    solved = True
    for constraintObj in constraintObjectQue:
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        debugPrint( 3, '  parsing %s, type:%s' % (constraintObj.Name, constraintObj.Type ))
        cArgs = [ variableManager, obj1Name, obj2Name, constraintObj.SubElement1,  constraintObj.SubElement2 ]
        try:
            if constraintObj.Type == 'plane':
                if constraintObj.SubElement2.startswith('Face'): #otherwise vertext
                    constraintSystem = AxisAlignmentUnion( constraintSystem, *cArgs,  constraintValue = constraintObj.directionConstraint )
                constraintSystem = PlaneOffsetUnion(   constraintSystem, *cArgs,  constraintValue = constraintObj.offset.Value)
            elif constraintObj.Type == 'angle_between_planes':
                constraintSystem = AngleUnion(  constraintSystem, *cArgs,  constraintValue = constraintObj.angle.Value*pi/180 )
            elif constraintObj.Type == 'axial':
                constraintSystem = AxisAlignmentUnion( constraintSystem, *cArgs, constraintValue = constraintObj.directionConstraint)
                constraintSystem =  AxisDistanceUnion( constraintSystem, *cArgs, constraintValue = 0)
            elif constraintObj.Type == 'circularEdge':
                constraintSystem = AxisAlignmentUnion( constraintSystem, *cArgs, constraintValue=constraintObj.directionConstraint)
                constraintSystem = AxisDistanceUnion( constraintSystem, *cArgs, constraintValue=0)
                constraintSystem = PlaneOffsetUnion( constraintSystem,  *cArgs, constraintValue=constraintObj.offset.Value)
            else:
                raise NotImplementedError, 'constraintType %s not supported yet' % constraintObj.Type
        except Assembly2SolverError, msg:
            FreeCAD.Console.PrintError('UNABLE TO SOLVE CONSTRAINTS! info:')
            FreeCAD.Console.PrintError(msg)
            solved = False
            break
        except:
            FreeCAD.Console.PrintError('UNABLE TO SOLVE CONSTRAINTS! info:')
            FreeCAD.Console.PrintError( traceback.format_exc())
            solved = False
            break
    if solved:
        debugPrint(4,'constraintSystem.X %s' % constraintSystem.X )
        variableManager.updateFreeCADValues( constraintSystem.X )
    elif QtGui.qApp <> None: #i.e. GUI active
        # http://www.blog.pythonlibrary.org/2013/04/16/pyside-standard-dialogs-and-message-boxes/
        flags = QtGui.QMessageBox.StandardButton.Yes 
        flags |= QtGui.QMessageBox.StandardButton.No
        flags |= QtGui.QMessageBox.Ignore
        message = """The assembly2 solver failed to satisfy the constraint "%s".

possible causes
  - impossible/contridictorary constraints have be specified, or  
  - the contraint problem is too difficult for the solver, or a 
  - bug in the assembly 2 workbench

potential solutions
  - redefine the constraint (popup menu item in the treeView)
  - delete constraint, and try again using a different constraint scheme.

Delete constraint "%s"? (press ignore to show the rejected solution)?
""" % (constraintObj.Name, constraintObj.Name)
        response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Solver Failure!", message, flags)
        if response == QtGui.QMessageBox.Yes:
            name = constraintObj.Name
            doc.removeObject( name )
            FreeCAD.Console.PrintError("removed constraint %s" % name )
        elif response == QtGui.QMessageBox.Ignore:
            variableManager.updateFreeCADValues( constraintSystem.getX() )
    return constraintSystem if solved else None

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






if __name__ == '__main__':
    import glob, argparse
    print('Testing assembly 2 solver on assemblies under tests/')
    parser = argparse.ArgumentParser(description="Test assembly 2 solver.")
    parser.add_argument('--lastTestCaseOnly', action='store_true')
    args = parser.parse_args()

    debugPrint.level = 4
    testFiles = sorted(glob.glob('tests/*.fcstd')) 
    if args.lastTestCaseOnly:
        testFiles = testFiles[-1:]
    for testFile in testFiles:
        print(testFile)
        doc =  FreeCAD.open(testFile)
        constraintSystem = solveConstraints( doc )
        if constraintSystem == None:
            exit()
        print('\n\n\n')
    print('All %i tests passed' % len(testFiles))
