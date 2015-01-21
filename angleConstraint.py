from assembly2lib import *
from assembly2lib import __dir__, wb_globals #variables not imported with * directive ...
from lib3D import *
from pivy import coin
from PySide import QtGui

class PlaneSelectionGate:
     def allow(self, doc, obj, sub):
          if not sub.startswith('Face'):
               return False
          ind = int( sub[4:]) -1 
          return str( obj.Shape.Faces[ind].Surface ) == '<Plane object>'

def parseSelection(selection, objectToUpdate=None):
     msg = 'To add an anlge constraint select two flat surfaces, each from a different part. Both of these parts should be imported using the assembly 2 work bench.'
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
          if str(face.Surface) <> '<Plane object>':
               QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
               return 
          cParms.append([s.ObjectName, faceInd])

     if objectToUpdate == None:
          cName = findUnusedObjectName('angleConstraint')
          debugPrint(2, "creating %s" % cName )
          c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
          c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'angle_between_planes'
          c.addProperty("App::PropertyString","Object1","ConstraintInfo","Object 1").Object1 = cParms[0][0]
          c.addProperty("App::PropertyInteger","FaceInd1","ConstraintInfo","Object 1 face index").FaceInd1 = cParms[0][1]
          c.addProperty("App::PropertyString","Object2","ConstraintInfo","Object 2").Object2 = cParms[1][0]
          c.addProperty("App::PropertyInteger","FaceInd2","ConstraintInfo","Object 2 face index").FaceInd2 = cParms[1][1]
          c.addProperty("App::PropertyFloat","degrees","ConstraintInfo","angle between the two planes in degrees")
     
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
