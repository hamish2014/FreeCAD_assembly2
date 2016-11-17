from assembly2lib import *
from lib3D import *
from pivy import coin
from PySide import QtGui

class AxialSelectionGate:
     def allow(self, doc, obj, sub):
          return ValidSelection(SelectionExObject(doc, obj, sub))

def ValidSelection(selectionExObj):
     return cylindricalPlaneSelected(selectionExObj)\
         or LinearEdgeSelected(selectionExObj)

def parseSelection(selection, objectToUpdate=None):
     validSelection = False
     if len(selection) == 2:
          s1, s2 = selection
          if s1.ObjectName <> s2.ObjectName:
               if ValidSelection(s1) and ValidSelection(s2):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                               [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]
     if not validSelection:
          msg = '''To add an axial constraint select two cylindrical surfaces or two straight lines, each from a different part. Selection made:
%s'''  % printSelection(selection)
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
          return 

     if objectToUpdate == None:
          cName = findUnusedObjectName('axialConstraint')
          debugPrint(2, "creating %s" % cName )
          c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
          c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'axial'
          c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
          c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
          c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
          c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
     
          c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
          c.directionConstraint = ["none","aligned","opposed"]
          c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo")
                         
          c.setEditorMode('Type',1)
          for prop in ["Object1","Object2","SubElement1","SubElement2"]:
               c.setEditorMode(prop, 1) 

          c.Proxy = ConstraintObjectProxy()
          c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly2/icons/axialConstraint.svg', True, cParms[1][2], cParms[0][2])
     else:
          debugPrint(2, "redefining %s" % objectToUpdate.Name )
          c = objectToUpdate
          c.Object1 = cParms[0][0]
          c.SubElement1 = cParms[0][1]
          c.Object2 = cParms[1][0]
          c.SubElement2 = cParms[1][1]
          updateObjectProperties(c)

     c.purgeTouched()
     c.Proxy.callSolveConstraints()
     repair_tree_view()

selection_text = '''Selection options:
  - cylindrical surface
  - edge '''

class AxialConstraintCommand:
     def Activated(self):
          selection = FreeCADGui.Selection.getSelectionEx()
          if len(selection) == 2:
               parseSelection( selection )
          else:
               FreeCADGui.Selection.clearSelection()
               ConstraintSelectionObserver( 
                    AxialSelectionGate(), 
                    parseSelection,
                    taskDialog_title ='add axial constraint', 
                    taskDialog_iconPath = self.GetResources()['Pixmap'], 
                    taskDialog_text = selection_text
                    )
     def GetResources(self): 
          return {
               'Pixmap' : ':/assembly2/icons/axialConstraint.svg', 
               'MenuText': 'Add axial constraint', 
               'ToolTip': 'Add an axial constraint between two objects'
               } 

FreeCADGui.addCommand('addAxialConstraint', AxialConstraintCommand())

class RedefineConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        ConstraintSelectionObserver( 
             AxialSelectionGate(), 
             self.UpdateConstraint,
             taskDialog_title ='redefine axial constraint', 
             taskDialog_iconPath = ':/assembly2/icons/axialConstraint.svg', 
             taskDialog_text = selection_text
             )
        #
        #if wb_globals.has_key('selectionObserver'): 
        #    wb_globals['selectionObserver'].stopSelectionObservation()
        #wb_globals['selectionObserver'] =  ConstraintSelectionObserver( AxialSelectionGate(), self.UpdateConstraint  )
    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)
    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineAxialConstraint', RedefineConstraintCommand())
