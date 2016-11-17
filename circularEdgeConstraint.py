from assembly2lib import *
from lib3D import *
from pivy import coin
from PySide import QtGui
         
class CircularEdgeSelectionGate:
    def allow(self, doc, obj, sub):
        return CircularEdgeSelected( SelectionExObject(doc, obj, sub) )

def parseSelection(selection, objectToUpdate=None, callSolveConstraints=True, lockRotation = False):
    validSelection = False
    if len(selection) == 2:
        s1, s2 = selection
        if s1.ObjectName <> s2.ObjectName:
            if CircularEdgeSelected(s1) and CircularEdgeSelected(s2):
                validSelection = True
                cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                           [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]

    if not validSelection:
          msg = '''To add a circular edge constraint select two circular edges, each from a different part. Selection made:
%s'''  % printSelection(selection)
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
          return 

    if objectToUpdate == None:
        cName = findUnusedObjectName('circularEdgeConstraint')
        debugPrint(2, "creating %s" % cName )
        c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
                
        c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'circularEdge'
        c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
        c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
        c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
        c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
    
        c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
        c.directionConstraint = ["none","aligned","opposed"]
        c.addProperty("App::PropertyDistance","offset","ConstraintInfo")
        c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo").lockRotation = lockRotation
    
        c.setEditorMode('Type',1)
        for prop in ["Object1","Object2","SubElement1","SubElement2"]:
            c.setEditorMode(prop, 1) 
        
        c.Proxy = ConstraintObjectProxy()
        c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly2/icons/circularEdgeConstraint.svg', True, cParms[1][2], cParms[0][2])
    else:
        debugPrint(2, "redefining %s" % objectToUpdate.Name )
        c = objectToUpdate
        c.Object1 = cParms[0][0]
        c.SubElement1 = cParms[0][1]
        c.Object2 = cParms[1][0]
        c.SubElement2 = cParms[1][1]
        updateObjectProperties(c)

    c.purgeTouched()
    if callSolveConstraints:
        c.Proxy.callSolveConstraints()  
        repair_tree_view()
    #FreeCADGui.Selection.clearSelection()
    #FreeCADGui.Selection.addSelection(c)
    return c
    

selection_text = '''Select 2 circular edges'''

class CircularEdgeConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 2:
            parseSelection( selection )
        else:
            FreeCADGui.Selection.clearSelection()
            ConstraintSelectionObserver( 
                CircularEdgeSelectionGate(), 
                parseSelection,
                taskDialog_title ='add circular edge constraint', 
                taskDialog_iconPath = self.GetResources()['Pixmap'], 
                taskDialog_text = selection_text
                )

    def GetResources(self): 
        return {
            'Pixmap' : ':/assembly2/icons/circularEdgeConstraint.svg' , 
            'MenuText': 'Add circular edge constraint', 
            'ToolTip': 'Add a circular edge constraint between two objects'
            } 

FreeCADGui.addCommand('addCircularEdgeConstraint', CircularEdgeConstraintCommand())


class RedefineCircularEdgeConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        ConstraintSelectionObserver( 
                CircularEdgeSelectionGate(), 
                self.UpdateConstraint,
                taskDialog_title ='redefine circular edge constraint', 
                taskDialog_iconPath = ':/assembly2/icons/circularEdgeConstraint.svg', 
                taskDialog_text = selection_text
                )

    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)

    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineCircularEdgeConstraint', RedefineCircularEdgeConstraintCommand())


class FlipLastConstraintsDirectionCommand:
    def Activated(self):
        constraints = [ obj for obj in FreeCAD.ActiveDocument.Objects 
                        if 'ConstraintInfo' in obj.Content ]
        if len(constraints) == 0:
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Command Aborted", 'Flip aborted since no assembly2 constraints in active document.')
            return
        lastConstraintAdded = constraints[-1]
        if hasattr( lastConstraintAdded, 'directionConstraint' ):
            if lastConstraintAdded.directionConstraint == "none":
                QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Command Aborted", 'Flip aborted since direction of the last constraint is unset')
                return
            if lastConstraintAdded.directionConstraint == "aligned":
                lastConstraintAdded.directionConstraint = "opposed"
            else:
                lastConstraintAdded.directionConstraint = "aligned"
        elif hasattr( lastConstraintAdded, 'angle' ):
            if lastConstraintAdded.angle.Value <= 0:
                lastConstraintAdded.angle = lastConstraintAdded.angle.Value + 180.0
            else:
                lastConstraintAdded.angle = lastConstraintAdded.angle.Value - 180.0
        else:
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Command Aborted", 'Flip aborted since the last constraint added does not have a direction or an angle attribute.')
            return
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self): 
        return {
            'Pixmap' : ':/assembly2/icons/flipConstraint.svg' , 
            'MenuText': "Flip last constraint's direction", 
            'ToolTip': 'Flip the direction of the last constraint added'
            } 

FreeCADGui.addCommand('flipLastConstraintsDirection', FlipLastConstraintsDirectionCommand())



class LockRotationOfLastConstraintAddedCommand:
    def Activated(self):
        constraints = [ obj for obj in FreeCAD.ActiveDocument.Objects 
                        if 'ConstraintInfo' in obj.Content ]
        if len(constraints) == 0:
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Command Aborted", 'Set LockRotation=True aborted since no assembly2 constraints in active document.')
            return
        lastConstraintAdded = constraints[-1]
        if hasattr( lastConstraintAdded, 'lockRotation' ):
            if not lastConstraintAdded.lockRotation:
                lastConstraintAdded.lockRotation = True
                FreeCAD.ActiveDocument.recompute()
            else:
                QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Information", 'Last constraints LockRotation attribute already set to True.')
        else:
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Command Aborted", 'Set LockRotation=True aborted since the last constraint added does not the LockRotation attribute.')
            return

    def GetResources(self): 
        return {
            'Pixmap' : ':/assembly2/icons/lockRotation.svg' , 
            'MenuText': "Set lockRotation->True for the last constraint added", 
            'ToolTip': 'Set lockRotation->True for the last constraint added'
            } 

FreeCADGui.addCommand('lockLastConstraintsRotation', LockRotationOfLastConstraintAddedCommand())
