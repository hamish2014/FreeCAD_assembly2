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

def parseSelection(selection):
    msg = 'To add a circular edge constraint select two circular edges, each from a different part. Both of these parts need to be imported using the assembly 2 work bench.'
    if len(selection) <> 2:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage",  msg )
        return
    cParms = [] # constraint parameters
    for s in selection:
        if not 'importPart' in s.Object.Content or len(s.SubElementNames) <> 1 or not s.SubElementNames[0].startswith('Edge'):
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
            return 
        edgeInd = int( s.SubElementNames[0][4:]) -1 
        edge = s.Object.Shape.Edges[edgeInd]
        if not all( hasattr(edge.Curve,a) for a in ['Axis','Center','Radius'] ):
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
            return 
        cParms.append([s.ObjectName, edgeInd])

    cName = findUnusedObjectName('circularEdgeConstraint')
    debugPrint(2, "creating %s" % cName )
    c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
                
    c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'circularEdge'
    c.addProperty("App::PropertyString","Object1","ConstraintInfo","Object 1").Object1 = cParms[0][0]
    c.addProperty("App::PropertyInteger","EdgeInd1","ConstraintInfo","Object 1 face index").EdgeInd1 = cParms[0][1]
    c.addProperty("App::PropertyString","Object2","ConstraintInfo","Object 2").Object2 = cParms[1][0]
    c.addProperty("App::PropertyInteger","EdgeInd2","ConstraintInfo","Object 2 face index").EdgeInd2 = cParms[1][1]
    
    c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
    c.directionConstraint = ["none","aligned","opposed"]
    c.addProperty("App::PropertyFloat","offset","ConstraintInfo")
    
    c.setEditorMode('Type',1)
    for prop in ["Object1","Object2","EdgeInd1","EdgeInd2"]:
        c.setEditorMode(prop, 1) 
        
    c.Proxy = ConstraintObjectProxy()
    c.Proxy.callSolveConstraints()    
    #FreeCADGui.Selection.clearSelection()
    #FreeCADGui.Selection.addSelection(c)
    

class CircularEdgeConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 2:
            parseSelection( selection )
        else:
            FreeCADGui.Selection.clearSelection()
            if wb_globals.has_key('selectionObserver'): 
                wb_globals['selectionObserver'].stopSelectionObservation()
            wb_globals['selectionObserver'] =  ConstraintSelectionObserver( CircularEdgeSelectionGate(), parseSelection  )

    def GetResources(self): 
        return {
            'Pixmap' : os.path.join( __dir__ , 'circularEdgeConstraint.svg' ) , 
            'MenuText': 'Add CircularEdge Constraint', 
            'ToolTip': 'Add an CircularEdge Constraint between two objects'
            } 

FreeCADGui.addCommand('addCircularEdgeConstraint', CircularEdgeConstraintCommand())

