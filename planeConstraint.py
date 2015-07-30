from assembly2lib import *
from assembly2lib import __dir__, wb_globals #variables not imported * directive ...
from lib3D import *
from pivy import coin
from PySide import QtGui

class PlaneSelectionGate:
     def allow(self, doc, obj, sub):
          if not sub.startswith('Face'):
               return False
          ind = int( sub[4:]) -1 
          return str( obj.Shape.Faces[ind].Surface ) == '<Plane object>'

class PlaneSelectionGate2:
     def allow(self, doc, obj, sub):
          if sub.startswith('Face'):
               ind = int( sub[4:]) -1 
               return str( obj.Shape.Faces[ind].Surface ) == '<Plane object>'
          elif sub.startswith('Vertex'):
               return True
          else:
               return False


def parseSelection(selection, objectToUpdate=None):
     validSelection = False
     if len(selection) == 2:
          s1, s2 = selection
          if s1.ObjectName <> s2.ObjectName:
               if not planeSelected(s1):
                    s2, s1 = s1, s2
               if planeSelected(s1) and (planeSelected(s2) or vertexSelected(s2)):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0] ],
                               [s2.ObjectName, s2.SubElementNames[0] ] ]
     if not validSelection:
          msg = '''Plane constraint requires a selection of either
- 2 planes, or
- 1 plane and 1 vertex 

Selection made:
%s'''  % printSelection(selection)
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
          return 

     if objectToUpdate == None:
          cName = findUnusedObjectName('planeConstraint')
          debugPrint(2, "creating %s" % cName )
          c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
          c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'plane'
          c.addProperty("App::PropertyString","Object1","ConstraintInfo")
          c.addProperty("App::PropertyString","SubElement1","ConstraintInfo")
          c.addProperty("App::PropertyString","Object2","ConstraintInfo")
          c.addProperty("App::PropertyString","SubElement2","ConstraintInfo")
          c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
     
          c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
          c.directionConstraint = ["none","aligned","opposed"]

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
         
class PlaneConstraintCommand:
     def Activated(self):
          selection = FreeCADGui.Selection.getSelectionEx()
          if len(selection) == 2:
               parseSelection( selection )
          else:
               FreeCADGui.Selection.clearSelection()
               ConstraintSelectionObserver( 
                    PlaneSelectionGate(), 
                    parseSelection, 
                    taskDialog_title ='add plane constraint', 
                    taskDialog_iconPath = self.GetResources()['Pixmap'], 
                    taskDialog_text = \
'''Selection 1 options:
  - plane
Selection 2 options:
  - plane
  - vertex ''',
                    secondSelectionGate = PlaneSelectionGate2() )
               
     def GetResources(self): 
          return {
               'Pixmap' : os.path.join( __dir__ , 'planeConstraint.svg' ) , 
               'MenuText': 'Add Plane Constraint', 
               'ToolTip': 'Add an Plane Constraint between two objects'
               } 

FreeCADGui.addCommand('addPlaneConstraint', PlaneConstraintCommand())


class RedefineConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        if wb_globals.has_key('selectionObserver'): 
            wb_globals['selectionObserver'].stopSelectionObservation()
        wb_globals['selectionObserver'] =  ConstraintSelectionObserver( PlaneSelectionGate(), self.UpdateConstraint, PlaneSelectionGate2()  )

    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)

    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefinePlaneConstraint', RedefineConstraintCommand())
