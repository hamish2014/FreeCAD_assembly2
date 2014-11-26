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

def parseSelection(selection):
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
     cName = findUnusedObjectName('axialConstraint')
     debugPrint(2, "creating %s" % cName )
     c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)

     c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'axial'
     c.addProperty("App::PropertyString","Object1","ConstraintInfo","Object 1").Object1 = cParms[0][0]
     c.addProperty("App::PropertyInteger","FaceInd1","ConstraintInfo","Object 1 face index").FaceInd1 = cParms[0][1]
     c.addProperty("App::PropertyString","Object2","ConstraintInfo","Object 2").Object2 = cParms[1][0]
     c.addProperty("App::PropertyInteger","FaceInd2","ConstraintInfo","Object 2 face index").FaceInd2 = cParms[1][1]
     c.addProperty("App::PropertyBool","enforceAxesDirections", "ConstraintInfo")
     c.addProperty("App::PropertyBool","axesDirectionsEqual", "ConstraintInfo")
                         
     c.setEditorMode('Type',1)
     for prop in ["Object1","Object2","FaceInd1","FaceInd2", "Type"]:
          c.setEditorMode(prop, 2) 

     c.Proxy = ConstraintObjectProxy()
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

class AxialConstraint(ConstraintPrototype): 
     def registerVariables( self ):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          obj1 = self.doc.getObject( self.constraintObj.Object1 )
          obj2 = self.doc.getObject( self.constraintObj.Object2 )
          surface1 =  obj1.Shape.Faces[self.constraintObj.FaceInd1].Surface
          surface2 =  obj2.Shape.Faces[self.constraintObj.FaceInd2].Surface
          self.a1_r = p1.rotate_undo( surface1.Axis ) #_r = relative to objects placement
          self.a2_r = p2.rotate_undo( surface2.Axis )
          self.c1_r = p1.rotate_and_then_move_undo( surface1.Center )
          #debugPrint(4, 'surface1.center %s, rotate_and_then_move_undo %s' % (surface1.Center, self.c1_r))
          self.c2_r = p2.rotate_and_then_move_undo( surface2.Center )
          self.enforceAxesDirections = self.constraintObj.enforceAxesDirections
          self.axesDirectionsEqual = self.constraintObj.axesDirectionsEqual

     def errors(self):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 = p1.rotate( self.a1_r )
          a2 = p2.rotate( self.a2_r )
          c1 = p1.rotate_and_then_move( self.c1_r )
          c2 = p2.rotate_and_then_move( self.c2_r )
          #debugPrint(4, 'a1 %s' % a1.__repr__())
          #debugPrint(4, 'a2 %s' % a2.__repr__())
          #debugPrint(4, 'c1 %s' % c1.__repr__())
          #debugPrint(4, 'c2 %s' % c2.__repr__())
          ax_prod = numpy.dot( a1, a2 )
          if not self.enforceAxesDirections :
               ax_const = (1 - abs(ax_prod))
          elif self.axesDirectionsEqual:
               ax_const = (1 - ax_prod)
          else:
               ax_const = (1 + ax_prod)

          return [
               ax_const * 10**4, 
               distance_between_two_axes_3_points(c1,a1,c2,a2)
               ]
