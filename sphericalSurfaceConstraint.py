from assembly2lib import *
from lib3D import *
from pivy import coin
from PySide import QtGui
         
class SphericalSurfaceSelectionGate:
    def allow(self, doc, obj, sub):
        if sub.startswith('Face'):
            face = getObjectFaceFromName( obj, sub)
            return str( face.Surface ).startswith('Sphere ')
        elif sub.startswith('Vertex'):
            return True
        else:
            return False


def parseSelection(selection, objectToUpdate=None):
    validSelection = False
    if len(selection) == 2:
        s1, s2 = selection
        if s1.ObjectName != s2.ObjectName:
            if ( vertexSelected(s1) or sphericalSurfaceSelected(s1)) \
                    and ( vertexSelected(s2) or sphericalSurfaceSelected(s2)):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                               [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]

    if not validSelection:
          msg = '''To add a spherical surface constraint select two spherical surfaces (or vertexs), each from a different part. Selection made:
%s'''  % printSelection(selection)
          QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
          return 

    if objectToUpdate == None:
        cName = findUnusedObjectName('sphericalSurfaceConstraint')
        debugPrint(2, "creating %s" % cName )
        c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
                
        c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'sphericalSurface'
        c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
        c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
        c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
        c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
    
        c.setEditorMode('Type',1)
        for prop in ["Object1","Object2","SubElement1","SubElement2"]:
            c.setEditorMode(prop, 1) 
        
        c.Proxy = ConstraintObjectProxy()
        c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly2/icons/sphericalSurfaceConstraint.svg', True, cParms[1][2], cParms[0][2])
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
  - spherical surface
  - vertex'''


class SphericalSurfaceConstraintCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 2:
            parseSelection( selection )
        else:
            FreeCADGui.Selection.clearSelection()
            ConstraintSelectionObserver( 
                SphericalSurfaceSelectionGate(), 
                parseSelection,
                taskDialog_title ='add spherical surface constraint', 
                taskDialog_iconPath = self.GetResources()['Pixmap'], 
                taskDialog_text = selection_text
                )

    def GetResources(self): 
        return {
            'Pixmap' : ':/assembly2/icons/sphericalSurfaceConstraint.svg', 
            'MenuText': 'Add a spherical surface constraint', 
            'ToolTip': 'Add a spherical surface constraint between two objects'
            } 

FreeCADGui.addCommand('addSphericalSurfaceConstraint', SphericalSurfaceConstraintCommand())


class RedefineSphericalSurfaceConstraintCommand:
    def Activated(self):
        self.constObject = FreeCADGui.Selection.getSelectionEx()[0].Object
        debugPrint(3,'redefining %s' % self.constObject.Name)
        FreeCADGui.Selection.clearSelection()
        ConstraintSelectionObserver( 
            SphericalSurfaceSelectionGate(), 
            self.UpdateConstraint,
            taskDialog_title ='redefine spherical surface constraint', 
            taskDialog_iconPath = ':/assembly2/icons/sphericalSurfaceConstraint.svg', 
            taskDialog_text = selection_text
            )
    def UpdateConstraint(self, selection):
        parseSelection( selection, self.constObject)

    def GetResources(self): 
        return { 'MenuText': 'Redefine' } 
FreeCADGui.addCommand('redefineSphericalSurfaceConstraint', RedefineSphericalSurfaceConstraintCommand())
