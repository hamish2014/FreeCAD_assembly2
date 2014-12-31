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
    constraintObjectQue = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content ]
    #doc.Objects already in tree order so no additional sorting / order checking required.
    objectNames = list( set( sum( [ [ c.Object1, c.Object2] for c in constraintObjectQue ], [] ) ) )
    variableManager = VariableManager( doc, objectNames )
    debugPrint(2,'variableManager.X0 %s' % variableManager.X0 )
    constraintSystem = FixedObjectSystem( variableManager, findBaseObject(doc, objectNames) )
    debugPrint(4, 'solveConstraints base system: %s' % constraintSystem.str() )
    def debugInfo():
        debugPrint(3, '  resulting system %s' % constraintSystem.str(addDOFs=debugPrint.level>3))

    for constraintObj in constraintObjectQue:
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        debugPrint( 3, '  parsing %s, type:%s' % (constraintObj.Name, constraintObj.Type ))
        if constraintObj.Type == 'plane':
            constraintSystem = AxisAlignmentUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.FaceInd1,  constraintObj.FaceInd2,  constraintObj.directionConstraint )
            debugInfo()
            constraintSystem = PlaneOffsetUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.FaceInd1, constraintObj.FaceInd2,  constraintObj.planeOffset)
            debugInfo()
        elif constraintObj.Type == 'angle_between_planes':
            constraintSystem = AngleUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.FaceInd1,  constraintObj.FaceInd2, cos(constraintObj.degrees / 180 * pi ) )
            debugInfo()
        elif constraintObj.Type == 'axial':
            constraintSystem = AxisAlignmentUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.FaceInd1,  constraintObj.FaceInd2,  constraintObj.directionConstraint,'cylinder')
            debugInfo()
            constraintSystem = AxisDistanceUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.FaceInd1,  constraintObj.FaceInd2,  0 ,'cylinder')
            debugInfo()
        elif constraintObj.Type == 'circularEdge':
            constraintSystem = AxisAlignmentUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.EdgeInd1,  constraintObj.EdgeInd2,  constraintObj.directionConstraint,'circle')
            debugInfo()
            constraintSystem = AxisDistanceUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.EdgeInd1,  constraintObj.EdgeInd2,  0 ,'circle')
            debugInfo()
            constraintSystem = PlaneOffsetUnion( variableManager, constraintSystem, obj1Name, obj2Name, constraintObj.EdgeInd1, constraintObj.EdgeInd2,  constraintObj.offset,'circle')
            debugInfo()                    
        else:
            raise RuntimeError, 'constraintType %s not supported yet' % constraintObj.Type
    debugPrint(3,'constraintSystem.X %s' % constraintSystem.X )
    variableManager.updateFreeCADValues( constraintSystem.X )
    return constraintSystem
    

#    if not solved:
#        FreeCAD.Console.PrintError("UNABLE TO SOLVE ASSEMBLY CONSTRAINTS.")
#        # http://www.blog.pythonlibrary.org/2013/04/16/pyside-standard-dialogs-and-message-boxes/
#        flags = QtGui.QMessageBox.StandardButton.Yes 
#        flags |= QtGui.QMessageBox.StandardButton.No
#        message = """The assembly2 failed to solve the specified constraints.
#This is due to either
#  - the contraint problem being too difficult for the solver, or
#  - impossible/contridictorary constraints have be specified.
#
#Either way, the solution is most likely to delete the problematic constraints, and try again using a different constraint scheme.
#Delete constraints [%s]?
# """ % ', '.join(vNames)
#        response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Solver Failure!",
#                                              message,
#                                              flags)
#        if response == QtGui.QMessageBox.Yes:
#            for name in vNames:
#                doc.removeObject(name)
#                FreeCAD.Console.PrintError("removed constraint %s" % name)
#        
#    #print(xOpt)


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
    print('Testing assembly 2 solver')
    import Part
    doc = FreeCAD.newDocument("testCase")
    debugPrint.level = 4
    
    obj1 = doc.addObject("Part::FeaturePython","part1")
    obj1.addProperty("App::PropertyBool","fixedPosition","importPart")
    obj1.fixedPosition = True
    obj1.Shape = Part.makeBox(2,3,2)

    obj2 = doc.addObject("Part::FeaturePython","part2")
    obj2.addProperty("App::PropertyBool","fixedPosition","importPart")
    obj2.Shape = Part.makeBox(1,1,1)
    obj2.Placement.Base.x = 6
    obj2.Placement.Base.y = 1
    obj2.Placement.Base.z = 2
    
    if False: #test to to make sure that the placement update works without FreeCADGui
        print('obj2.Placement.Base %s \t obj2.Placement.Rotation %s' % (obj2.Placement.Base, obj2.Placement.Rotation))
        print('obj2.Shape.Faces[5].Surface: Position %s' % repr(obj2.Shape.Faces[5].Surface.Position))
        print('obj2.Shape.Faces[5].Surface: Axis %s' % repr(obj2.Shape.Faces[5].Surface.Axis))
        obj2.Placement.Base.x = 4
        print('obj2.Placement.Base %s \t obj2.Placement.Rotation %s' % (obj2.Placement.Base, obj2.Placement.Rotation))
        print('obj2.Shape.Faces[5].Surface: Position %s' % repr(obj2.Shape.Faces[5].Surface.Position))
        print('obj2.Shape.Faces[5].Surface: Axis %s' % repr(obj2.Shape.Faces[5].Surface.Axis))
        obj2.Placement.Rotation.Q = euler_to_quaternion( 0, pi/2, 0 )
        print('obj2.Placement.Base %s \t obj2.Placement.Rotation %s' % (obj2.Placement.Base, obj2.Placement.Rotation))
        print('obj2.Shape.Faces[5].Surface: Position %s' % repr(obj2.Shape.Faces[5].Surface.Position))
        print('obj2.Shape.Faces[5].Surface: Axis %s' % repr(obj2.Shape.Faces[5].Surface.Axis))
        exit()

    saveTo = '/tmp/assembly_test_case_1_unassembled.fcstd'
    print('saving %s' % saveTo)
    doc.saveAs(saveTo)
    
    print('adding a plane constraints')
    def addPlaneConstraint(document, name, objName1, face1, objName2, face2, directionOption):
        c = document.addObject("App::FeaturePython", name)
        c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'plane'
        c.addProperty("App::PropertyString","Object1","ConstraintInfo","Object 1").Object1 = objName1
        c.addProperty("App::PropertyInteger","FaceInd1","ConstraintInfo","Object 1 face index").FaceInd1 = face1
        c.addProperty("App::PropertyString","Object2","ConstraintInfo","Object 2").Object2 = objName2
        c.addProperty("App::PropertyInteger","FaceInd2","ConstraintInfo","Object 2 face index").FaceInd2 = face2
        c.addProperty("App::PropertyFloat","planeOffset","ConstraintInfo")
        c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
        c.directionConstraint = ["none","aligned","opposed"]
        c.directionConstraint = ["none","aligned","opposed"][directionOption]
        c.Proxy = ConstraintObjectProxy()
        
    addPlaneConstraint( doc, 'planeConstraint1', 'part1',1, 'part2',5, 2)
    addPlaneConstraint( doc, 'planeConstraint2', 'part2',1, 'part1',3, 0)
    addPlaneConstraint( doc, 'planeConstraint3', 'part2',2, 'part1',5, 0)

    solveConstraints( doc )

    saveTo = '/tmp/assembly_test_case_1_assembled.fcstd'
    print('saving %s' % saveTo)
    doc.saveAs(saveTo)

    print('\n')
    #doc.recompute() #recompute not required for position updates.!
    solveConstraints( doc )
