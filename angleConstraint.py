from assembly2lib import *
from assembly2lib import __dir__, wb_globals #variables not imported with * directive ...
from lib3D import *
from pivy import coin
from PySide import QtGui

class PlaneSelectionGate:
     def allow(self, doc, obj, sub):
          if sub.startswith('Face'):
               face = getObjectFaceFromName( obj, sub)
               return str( face.Surface ) == '<Plane object>'
          elif sub.startswith('Edge'):
               edge = getObjectEdgeFromName( obj, sub)
               return isinstance(edge.Curve, Part.Line)
          else:
               return False

def parseSelection(selection, objectToUpdate=None):
     validSelection = False
     if len(selection) == 2:
          s1, s2 = selection
          if s1.ObjectName <> s2.ObjectName:
               if ( planeSelected(s1) or LinearEdgeSelected(s1)) \
                        and ( planeSelected(s2) or LinearEdgeSelected(s2)):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0] ],
                               [s2.ObjectName, s2.SubElementNames[0] ] ]
     if not validSelection:
          msg = '''Angle constraint requires a selection of 2 planes or two straight lines, each from different objects.Selection made:
%s'''  % printSelection(selection)
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
          return 

     if objectToUpdate == None:
          cName = findUnusedObjectName('angleConstraint')
          debugPrint(2, "creating %s" % cName )
          c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
          c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'angle_between_planes'
          c.addProperty("App::PropertyString","Object1","ConstraintInfo")
          c.addProperty("App::PropertyString","SubElement1","ConstraintInfo")
          c.addProperty("App::PropertyString","Object2","ConstraintInfo")
          c.addProperty("App::PropertyString","SubElement2","ConstraintInfo")
          c.addProperty("App::PropertyAngle","angle","ConstraintInfo")
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
         
class AngleConstraintCommand:
     def Activated(self):
          selection = FreeCADGui.Selection.getSelectionEx()
          if len(selection) == 2:
               parseSelection( selection )
          else:
               FreeCADGui.Selection.clearSelection()
               if wb_globals.has_key('selectionObserver'): 
                    wb_globals['selectionObserver'].stopSelectionObservation()
               wb_globals['selectionObserver'] =  ConstraintSelectionObserver( PlaneSelectionGate(), parseSelection  )
               
     def GetResources(self): 
          msg = 'create an angular constraint between two planes'
          return {
               'Pixmap' : os.path.join( __dir__ , 'angleConstraint.svg' ) , 
               'MenuText': msg, 
               'ToolTip': msg,
               } 

FreeCADGui.addCommand('addAngleConstraint', AngleConstraintCommand())


class RedefineConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        if wb_globals.has_key('selectionObserver'): 
            wb_globals['selectionObserver'].stopSelectionObservation()
        wb_globals['selectionObserver'] =  ConstraintSelectionObserver( PlaneSelectionGate(), self.UpdateConstraint  )

    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)

    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineAngleConstraint', RedefineConstraintCommand())
