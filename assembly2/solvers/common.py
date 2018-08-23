from assembly2.core import debugPrint


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
        debugPrint( 1, 'assembly 2 solver: assigning %s, %s a fixed position' % (objectNames[0], doc.getObject(objectNames[0]).Label))
        return objectNames[0]

def constraintsObjectsAllExist( doc ):
    objectNames = [ obj.Name for obj in doc.Objects if not 'ConstraintInfo' in obj.Content ]
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            if not (obj.Object1 in objectNames and obj.Object2 in objectNames):
                flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.Abort
                message = "%s is refering to an object no longer in the assembly. Delete constraint? otherwise abort solving." % obj.Name
                response = QtGui.QMessageBox.critical(QtGui.QApplication.activeWindow(), "Broken Constraint", message, flags )
                if response == QtGui.QMessageBox.Yes:
                    FreeCAD.Console.PrintError("removing constraint %s" % obj.Name)
                    doc.removeObject(obj.Name)
                else:
                    missingObject = obj.Object2 if obj.Object1 in objectNames else obj.Object1
                    FreeCAD.Console.PrintError("aborted solving constraints due to %s refering the non-existent object %s" % (obj.Name, missingObject))
                    return False
    return True
