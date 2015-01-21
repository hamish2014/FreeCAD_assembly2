from assembly2lib import *
from assembly2lib import __dir__, wb_globals #variables not imported * directive ...
from lib3D import *
from pivy import coin
from PySide import QtGui

class AxialSelectionGate:
     def allow(self, doc, obj, sub):
          if not sub.startswith('Face'):
               return False
          ind = int( sub[4:]) -1 
          return hasattr( obj.Shape.Faces[ind].Surface, 'Radius' )

def parseSelection(selection, objectToUpdate=None):
     msg = 'To add an axial constraint select two cylindrical surfaces, each from a different part. Both of these parts should be imported using the assembly 2 work bench.'
     if len(selection) <> 2:
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage",  msg )
          return
     cParms = [] # constraint parameters
     for s in selection:
          if not 'importPart' in s.Object.Content or len(s.SubElementNames) <> 1 or not s.SubElementNames[0].startswith('Face'):
               QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
               return 
          faceInd = int( s.SubElementNames[0][4:]) -1 
          face = s.Object.Shape.Faces[faceInd]
          if not all( hasattr(face.Surface,a) for a in ['Axis','Center','Radius'] ):
               QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
               return 
          cParms.append([s.ObjectName, faceInd])

     if objectToUpdate == None:
          cName = findUnusedObjectName('axialConstraint')
          debugPrint(2, "creating %s" % cName )
          c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
          c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'axial'
          c.addProperty("App::PropertyString","Object1","ConstraintInfo","Object 1").Object1 = cParms[0][0]
          c.addProperty("App::PropertyInteger","FaceInd1","ConstraintInfo","Object 1 face index").FaceInd1 = cParms[0][1]
          c.addProperty("App::PropertyString","Object2","ConstraintInfo","Object 2").Object2 = cParms[1][0]
          c.addProperty("App::PropertyInteger","FaceInd2","ConstraintInfo","Object 2 face index").FaceInd2 = cParms[1][1]
     
          c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
          c.directionConstraint = ["none","aligned","opposed"]
                         
          c.setEditorMode('Type',1)
          for prop in ["Object1","Object2","FaceInd1","FaceInd2"]:
               c.setEditorMode(prop, 1) 

          c.Proxy = ConstraintObjectProxy()
     else:
          debugPrint(2, "redefining %s" % objectToUpdate.Name )
          c = objectToUpdate
          c.Object1 = cParms[0][0]
          c.FaceInd1 = cParms[0][1]
          c.Object2 = cParms[1][0]
          c.FaceInd2 = cParms[1][1]

     c.Proxy.callSolveConstraints()
         
class AxialConstraintCommand:
     def Activated(self):
          selection = FreeCADGui.Selection.getSelectionEx()
          if len(selection) == 2:
               parseSelection( selection )
          else:
               FreeCADGui.Selection.clearSelection()
               if wb_globals.has_key('selectionObserver'): 
                    wb_globals['selectionObserver'].stopSelectionObservation()
               wb_globals['selectionObserver'] =  ConstraintSelectionObserver( AxialSelectionGate(), parseSelection  )
     def GetResources(self): 
          return {
               'Pixmap' : os.path.join( __dir__ , 'axialConstraint.svg' ) , 
               'MenuText': 'Add Axial Constraint', 
               'ToolTip': 'Add an Axial Constraint between two objects'
               } 

FreeCADGui.addCommand('addAxialConstraint', AxialConstraintCommand())

class RedefineConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        if wb_globals.has_key('selectionObserver'): 
            wb_globals['selectionObserver'].stopSelectionObservation()
        wb_globals['selectionObserver'] =  ConstraintSelectionObserver( AxialSelectionGate(), self.UpdateConstraint  )
    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)
    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineAxialConstraint', RedefineConstraintCommand())
