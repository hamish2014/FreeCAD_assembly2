'''
Used for importing parts from other FreeCAD documents.
When update parts is executed, this library import or updates the parts in the assembly document.
'''
from assembly2lib import *
from assembly2lib import __dir__
from PySide import QtGui
import os, numpy

class Proxy_importPart:
    def execute(self, shape):
        pass

def importPart( filename, partName=None ):
    updateExistingPart = partName <> None
    if not updateExistingPart:
        FreeCAD.Console.PrintMessage("importing part from %s\n" % filename)
    doc_already_open = filename in [ d.FileName for d in FreeCAD.listDocuments().values() ] 
    debugPrint(4, "%s open already %s" % (filename, doc_already_open))
    if not doc_already_open:
        currentDoc = FreeCAD.ActiveDocument.Name
        FreeCAD.open(filename)
        FreeCAD.setActiveDocument(currentDoc)
    doc = [ d for d in FreeCAD.listDocuments().values()
            if d.FileName == filename][0]
    debugPrint(2, '%s objects %s' % (doc.Name, doc.Objects))
    visibleObjects = [ obj for obj in doc.Objects
                       if hasattr(obj,'ViewObject') and obj.ViewObject.isVisible()
                       and hasattr(obj,'Shape') and len(obj.Shape.Faces) > 0] # len(obj.Shape.Faces) > 0 to avoid sketches
    if len(visibleObjects) <> 1:
        if not updateExistingPart:
            msg = "A part can only be imported from a FreeCAD document with exactly one visible part. Aborting operation"
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
        else:
            msg = "Error updating part from %s: A part can only be imported from a FreeCAD document with exactly one visible part. Aborting update of %s" % (partName, filename)
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
        #QtGui.QMessageBox.warning( QtGui.qApp.activeWindow(), "Value Error!", msg, QtGui.QMessageBox.StandardButton.Ok )
    else:
        obj_to_copy = visibleObjects[0]
        if updateExistingPart:
            obj = FreeCAD.ActiveDocument.getObject(partName)
            prevPlacement = obj.Placement
        else:
            partName = findUnusedObjectName( doc.Name + '_import' )
            obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
            obj.addProperty("App::PropertyString","sourceFile","importPart").sourceFile = filename
            obj.setEditorMode("sourceFile",1)  
            obj.addProperty("App::PropertyBool","fixedPosition","importPart")
            obj.fixedPosition = not any([i.fixedPosition for i in FreeCAD.ActiveDocument.Objects if hasattr(i, 'fixedPosition') ])
        obj.Shape = obj_to_copy.Shape.copy()
        # would this work?:   obj.ViewObject = visibleObjects[0].ViewObject  
        if updateExistingPart:
            obj.Placement = prevPlacement
            obj.touch()
        else:
            #obj.ViewObject.Proxy = ViewProviderProxy_importPart()
            obj.ViewObject.Proxy = 0
            for p in obj_to_copy.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
                if hasattr(obj.ViewObject, p):
                    setattr(obj.ViewObject, p, getattr(obj_to_copy.ViewObject, p))
            obj.Proxy = Proxy_importPart()
            if not updateExistingPart and not obj.fixedPosition: #then offset new part slightly
                obj.Placement.Base.x = 42*numpy.random.rand()
                obj.Placement.Base.y = 42*numpy.random.rand()
                obj.Placement.Base.z = 42*numpy.random.rand()

    if not doc_already_open: #then close again
        FreeCAD.closeDocument(doc.Name)
        FreeCAD.setActiveDocument(currentDoc)


class ImportPartCommand:
    def Activated(self):
        filename, filetype = QtGui.QFileDialog.getOpenFileName( 
            QtGui.qApp.activeWindow(),
            "Select FreeCAD document to import part from",
            os.path.dirname(FreeCAD.ActiveDocument.FileName),
            "FreeCAD Document (*.fcstd)"
            )
        if filename == '':
            return
        importPart( filename )
        FreeCAD.ActiveDocument.recompute()

       
    def GetResources(self): 
        return {
            'Pixmap' : os.path.join( __dir__ , 'importPart.svg' ) , 
            'MenuText': 'Import a part from another FreeCAD document', 
            'ToolTip': 'Import a part from another FreeCAD document'
            } 

FreeCADGui.addCommand('importPart', ImportPartCommand())


class UpdateImportedPartsCommand:
    def Activated(self):
        for obj in FreeCAD.ActiveDocument.Objects:
            if hasattr(obj, 'sourceFile'):
                importPart( obj.sourceFile, obj.Name )
        FreeCAD.ActiveDocument.recompute()

       
    def GetResources(self): 
        return {
            'Pixmap' : os.path.join( __dir__ , 'importPart_update.svg' ) , 
            'MenuText': 'Update parts imported into the assembly', 
            'ToolTip': 'Update parts imported into the assembly'
            } 

FreeCADGui.addCommand('updateImportedPartsCommand', UpdateImportedPartsCommand())
