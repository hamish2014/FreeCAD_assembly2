from assembly2lib import *
from assembly2lib import __dir__, wb_globals #variables not imported * directive ...
from lib3D import *
from pivy import coin
from PySide import QtGui
         
class CircularEdgeSelectionGate:
    def allow(self, doc, obj, sub):
        if not sub.startswith('Edge'):
            return False
        ##if doc.Name <> self.docName: #deemed unnessary
        ##    return False
        #FreeCAD.Console.PrintMessage("addSelection %s-%s-%s\n" % (doc.Name, obj.Name, sub))
        edgeInd = int( sub[4:]) -1 
        return hasattr( obj.Shape.Edges[edgeInd].Curve, 'Radius' )

def parseSelection(selection, objectToUpdate=None):
    validSelection = False
    if len(selection) == 2:
        s1, s2 = selection
        if s1.ObjectName <> s2.ObjectName:
            if CircularEdgeSelected(s1) and CircularEdgeSelected(s2):
                validSelection = True
                cParms = [ [s1.ObjectName, s1.SubElementNames[0] ],
                           [s2.ObjectName, s2.SubElementNames[0] ] ]

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
        c.addProperty("App::PropertyString","Object1","ConstraintInfo")
        c.addProperty("App::PropertyString","SubElement1","ConstraintInfo")
        c.addProperty("App::PropertyString","Object2","ConstraintInfo")
        c.addProperty("App::PropertyString","SubElement2","ConstraintInfo")
    
        c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
        c.directionConstraint = ["none","aligned","opposed"]
        c.addProperty("App::PropertyDistance","offset","ConstraintInfo")
        c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo")
    
        c.setEditorMode('Type',1)
        for prop in ["Object1","Object2","SubElement1","SubElement2"]:
            c.setEditorMode(prop, 1) 
        
        c.Proxy = ConstraintObjectProxy()
    else:
        debugPrint(2, "redefining %s" % objectToUpdate.Name )
        c = objectToUpdate
        updateObjectProperties(c)

    c.Object1 = cParms[0][0]
    c.SubElement1 = cParms[0][1]
    c.Object2 = cParms[1][0]
    c.SubElement2 = cParms[1][1]

    c.Proxy.callSolveConstraints()    
    #FreeCADGui.Selection.clearSelection()
    #FreeCADGui.Selection.addSelection(c)
    

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
            'Pixmap' : os.path.join( __dir__ , 'circularEdgeConstraint.svg' ) , 
            'MenuText': 'Add CircularEdge Constraint', 
            'ToolTip': 'Add an CircularEdge Constraint between two objects'
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
                taskDialog_iconPath = os.path.join( __dir__ , 'circularEdgeConstraint.svg' ), 
                taskDialog_text = selection_text
                )

    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)

    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineCircularEdgeConstraint', RedefineCircularEdgeConstraintCommand())
