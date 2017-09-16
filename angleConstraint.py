from assembly2lib import *
from lib3D import *
from pivy import coin
from PySide import QtGui

__dir2__ = os.path.dirname(__file__)
GuiPath = os.path.join( __dir2__, 'Gui' )
class PlaneSelectionGate:
     def allow(self, doc, obj, sub):
          s = SelectionExObject(doc, obj, sub)
          return planeSelected(s) or LinearEdgeSelected(s) or AxisOfPlaneSelected(s)

def parseSelection(selection, objectToUpdate=None):
     validSelection = False
     if len(selection) == 2:
          s1, s2 = selection
          if s1.ObjectName <> s2.ObjectName:
               if ( planeSelected(s1) or LinearEdgeSelected(s1) or AxisOfPlaneSelected(s1)) \
                        and ( planeSelected(s2) or LinearEdgeSelected(s2) or AxisOfPlaneSelected(s2)):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                               [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]
     if not validSelection:
          msg = '''Angle constraint requires a selection of 2 planes or two straight lines/axis, each from different objects.Selection made:
%s'''  % printSelection(selection)
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
          return 

     if objectToUpdate is None:
          cName = findUnusedObjectName('angleConstraint')
          debugPrint(2, "creating %s" % cName )
          c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
          c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'angle_between_planes'
          c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
          c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
          c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
          c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
          c.addProperty("App::PropertyAngle","angle","ConstraintInfo")
          c.Object1 = cParms[0][0]
          c.SubElement1 = cParms[0][1]
          c.Object2 = cParms[1][0]
          c.SubElement2 = cParms[1][1]
          for prop in ["Object1","Object2","SubElement1","SubElement2","Type"]:
               c.setEditorMode(prop, 1) 
          c.Proxy = ConstraintObjectProxy()
          c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly2/icons/angleConstraint.svg', True, cParms[1][2], cParms[0][2])
     else:
          debugPrint(2, "redefining %s" % objectToUpdate.Name )
          c = objectToUpdate
          c.Object1 = cParms[0][0]
          c.SubElement1 = cParms[0][1]
          c.Object2 = cParms[1][0]
          c.SubElement2 = cParms[1][1]
          updateObjectProperties(c)
     constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
     with open(constraintFile, 'w') as outfile:
          outfile.write(make_string(s1.ObjectName)+'\n'+str(s1.Object.Placement.Base)+'\n'+str(s1.Object.Placement.Rotation)+'\n')        
          outfile.write(make_string(s2.ObjectName)+'\n'+str(s2.Object.Placement.Base)+'\n'+str(s2.Object.Placement.Rotation)+'\n')        
     constraints = [ obj for obj in FreeCAD.ActiveDocument.Objects if 'ConstraintInfo' in obj.Content ]
     #print constraints
     if len(constraints) > 0:
          constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
          if os.path.exists(constraintFile):
              with open(constraintFile, 'a') as outfile:
                  lastConstraintAdded = constraints[-1]
                  outfile.write(make_string(lastConstraintAdded.Name)+'\n')
     
     c.purgeTouched()
     c.Proxy.callSolveConstraints()
     repair_tree_view()
         

selection_text = '''Selection options:
  - plane surface
  - edge 
  - axis of plane selected'''

class AngleConstraintCommand:
     def Activated(self):
          selection = FreeCADGui.Selection.getSelectionEx()
          sel = FreeCADGui.Selection.getSelection()
          if len(selection) == 2:
               parseSelection( selection )
          else:
               FreeCADGui.Selection.clearSelection()
               ConstraintSelectionObserver( 
                    PlaneSelectionGate(), 
                    parseSelection,
                    taskDialog_title ='add angular constraint', 
                    taskDialog_iconPath = self.GetResources()['Pixmap'], 
                    taskDialog_text = selection_text )
               
     def GetResources(self): 
          msg = 'Create an angular constraint between two planes'
          return {
               'Pixmap' : ':/assembly2/icons/angleConstraint.svg', 
               'MenuText': msg, 
               'ToolTip': msg,
               } 

FreeCADGui.addCommand('addAngleConstraint', AngleConstraintCommand())


class RedefineConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        ConstraintSelectionObserver( 
             PlaneSelectionGate(), 
             self.UpdateConstraint,
             taskDialog_title ='redefine angular constraint', 
             taskDialog_iconPath = ':/assembly2/icons/angleConstraint.svg', 
             taskDialog_text = selection_text )

    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)

    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineAngleConstraint', RedefineConstraintCommand())
