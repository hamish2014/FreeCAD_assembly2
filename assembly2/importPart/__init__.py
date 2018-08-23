'''
Used for importing parts from other FreeCAD documents.
When update parts is executed, this library import or updates the parts in the assembly document.
'''

from assembly2.core import *
from assembly2.core import __dir__
from assembly2.lib3D import *
from assembly2.solvers import solveConstraints
from assembly2.utils.muxAssembly import (
    muxObjects,
    Proxy_muxAssemblyObj,
    muxMapColors
)
from viewProviderProxy import ImportedPartViewProviderProxy, group_constraints_under_parts
import Part
from PySide import QtGui
import os, numpy, shutil, copy, time

from fcstd_parser import Fcstd_File_Parser
from importPath import *
from selectionMigration import *

def importPart( filename, partName=None, doc_assembly=None ):
    if doc_assembly == None:
        doc_assembly = FreeCAD.ActiveDocument
    updateExistingPart = partName != None
    if updateExistingPart:
        FreeCAD.Console.PrintMessage("updating part %s from %s\n" % (partName,filename))
    else:
        FreeCAD.Console.PrintMessage("importing part from %s\n" % filename)
    doc_already_open = filename in [ d.FileName for d in FreeCAD.listDocuments().values() ]
    debugPrint(4, "%s open already %s" % (filename, doc_already_open))
    if doc_already_open:
        doc = [ d for d in FreeCAD.listDocuments().values() if d.FileName == filename][0]
        close_doc = False
    else:
        if filename.lower().endswith('.fcstd'):
            doc = Fcstd_File_Parser( filename )
            close_doc = False
        else: #trying shaping import http://forum.freecadweb.org/viewtopic.php?f=22&t=12434&p=99772#p99772x
            import ImportGui
            doc = FreeCAD.newDocument( os.path.basename(filename) )
            shapeobj = ImportGui.insert(filename,doc.Name)
            close_doc = True

    visibleObjects = [ obj for obj in doc.Objects
                       if hasattr(obj,'ViewObject') and obj.ViewObject.isVisible()
                       and hasattr(obj,'Shape') and len(obj.Shape.Faces) > 0 and 'Body' not in obj.Name] # len(obj.Shape.Faces) > 0 to avoid sketches, skip Body

    debugPrint(3, '%s objects %s' % (doc.Name, doc.Objects))
    if any([ 'importPart' in obj.Content for obj in doc.Objects]) and not len(visibleObjects) == 1:
        subAssemblyImport = True
        debugPrint(2, 'Importing subassembly from %s' % filename)
        tempPartName = 'import_temporary_part'
        obj_to_copy = doc_assembly.addObject("Part::FeaturePython",tempPartName)
        obj_to_copy.Proxy = Proxy_muxAssemblyObj()
        obj_to_copy.ViewObject.Proxy = ImportedPartViewProviderProxy()
        obj_to_copy.Shape =  muxObjects(doc)
        if (not updateExistingPart) or \
                (updateExistingPart and getattr( doc_assembly.getObject(partName),'updateColors',True)):
            muxMapColors(doc, obj_to_copy)
    else:
        subAssemblyImport = False
        if len(visibleObjects) != 1:
            if not updateExistingPart:
                msg = "A part can only be imported from a FreeCAD document with exactly one visible part. Aborting operation"
                QtGui.QMessageBox.information(  QtGui.QApplication.activeWindow(), "Value Error", msg )
            else:
                msg = "Error updating part from %s: A part can only be imported from a FreeCAD document with exactly one visible part. Aborting update of %s" % (partName, filename)
            QtGui.QMessageBox.information(  QtGui.QApplication.activeWindow(), "Value Error", msg )
        #QtGui.QMessageBox.warning( QtGui.QApplication.activeWindow(), "Value Error!", msg, QtGui.QMessageBox.StandardButton.Ok )
            return
        obj_to_copy  = visibleObjects[0]

    if updateExistingPart:
        obj = doc_assembly.getObject(partName)
        prevPlacement = obj.Placement
        if not hasattr(obj, 'updateColors'):
            obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True
        importUpdateConstraintSubobjects( doc_assembly, obj, obj_to_copy )
    else:
        partName = findUnusedObjectName( doc.Label + '_', document=doc_assembly )
        try:
            obj = doc_assembly.addObject("Part::FeaturePython",partName)
        except UnicodeEncodeError:
            safeName = findUnusedObjectName('import_', document=doc_assembly)
            obj = doc_assembly.addObject("Part::FeaturePython", safeName)
            obj.Label = findUnusedLabel( doc.Label + '_', document=doc_assembly )
        obj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = filename
        obj.addProperty("App::PropertyFloat", "timeLastImport","importPart")
        obj.setEditorMode("timeLastImport",1)
        obj.addProperty("App::PropertyBool","fixedPosition","importPart")
        obj.fixedPosition = not any([i.fixedPosition for i in doc_assembly.Objects if hasattr(i, 'fixedPosition') ])
        obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True
    obj.Shape = obj_to_copy.Shape.copy()
    if updateExistingPart:
        obj.Placement = prevPlacement
    else:
        # for Fcstd_File_Parser not all properties are implemented...
        for p in obj_to_copy.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
            if hasattr(obj.ViewObject, p) and p not in ['DiffuseColor']:
                try:
                    setattr(obj.ViewObject, p, getattr(obj_to_copy.ViewObject, p))
                except Exception as msg:
                    FreeCAD.Console.PrintWarning('Unable to setattr(obj.ViewObject, %s, %s)\n' % (p, getattr(obj_to_copy.ViewObject, p) ))
        obj.ViewObject.Proxy = ImportedPartViewProviderProxy()
    if getattr(obj,'updateColors',True) and hasattr( obj_to_copy.ViewObject, 'DiffuseColor'):
        obj.ViewObject.DiffuseColor = copy.copy( obj_to_copy.ViewObject.DiffuseColor )
        #obj.ViewObject.Transparency = copy.copy( obj_to_copy.ViewObject.Transparency )   # .Transparency property
        tsp = copy.copy( obj_to_copy.ViewObject.Transparency )   #  .Transparency workaround for FC 0.17 @ Nov 2016
        if tsp < 100 and tsp!=0:
            obj.ViewObject.Transparency = tsp+1
        if tsp == 100:
            obj.ViewObject.Transparency = tsp-1
        obj.ViewObject.Transparency = tsp   # .Transparency workaround end
    obj.Proxy = Proxy_importPart()
    obj.timeLastImport = os.path.getmtime( filename )
    #clean up
    if subAssemblyImport:
        doc_assembly.removeObject(tempPartName)
    if close_doc: 
        FreeCAD.closeDocument( doc.Name )
        FreeCAD.setActiveDocument( doc_assembly.Name )
        FreeCAD.ActiveDocument = doc_assembly
    return obj

class Proxy_importPart:
    def execute(self, shape):
        pass

class ImportPartCommand:
    def Activated(self):
        if FreeCADGui.ActiveDocument == None:
            FreeCAD.newDocument()
        view = FreeCADGui.activeDocument().activeView()
        #filename, filetype = QtGui.QFileDialog.getOpenFileName(
        #    QtGui.QApplication.activeWindow(),
        #    "Select FreeCAD document to import part from",
        #    "",# "" is the default, os.path.dirname(FreeCAD.ActiveDocument.FileName),
        #    "FreeCAD Document (*.fcstd)"
        #    )
        dialog = QtGui.QFileDialog(
            QtGui.QApplication.activeWindow(),
            "Select FreeCAD document to import part from"
            )
        dialog.setNameFilter("Supported Formats (*.FCStd *.brep *.brp *.imp *.iges *.igs *.obj *.step *.stp);;All files (*.*)")
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
        else:
            return
        importedObject = importPart( filename )
        FreeCAD.ActiveDocument.recompute()
        if not importedObject.fixedPosition: #will be true for the first imported part
            PartMover( view, importedObject )
        else:
            from PySide import QtCore
            self.timer = QtCore.QTimer()
            QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.GuiViewFit)
            self.timer.start( 200 ) #0.2 seconds

    def GuiViewFit(self):
        FreeCADGui.SendMsgToActiveView("ViewFit")
        self.timer.stop()

    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/importPart.svg',
            'MenuText': 'Import a part from another FreeCAD document',
            'ToolTip': 'Import a part from another FreeCAD document'
            }
FreeCADGui.addCommand('assembly2_importPart', ImportPartCommand())


class UpdateImportedPartsCommand:
    def Activated(self):
        #disable proxies solving the system as their objects are updated
        doc_assembly = FreeCAD.ActiveDocument
        solve_assembly_constraints = False
        YesToAll_clicked = False
        for obj in doc_assembly.Objects:
            if hasattr(obj, 'sourceFile'):
                if not hasattr( obj, 'timeLastImport'):
                    obj.addProperty("App::PropertyFloat", "timeLastImport","importPart") #should default to zero which will force update.
                    obj.setEditorMode("timeLastImport",1)
                if not os.path.exists( obj.sourceFile ) and  path_rel_to_abs( obj.sourceFile ) is None:
                    debugPrint( 3, '%s.sourceFile %s is missing, attempting to repair it' % (obj.Name,  obj.sourceFile) )
                    replacement = None
                    aFolder, aFilename = posixpath.split( doc_assembly.FileName )
                    sParts = path_split( posixpath, obj.sourceFile)
                    debugPrint( 3, '  obj.sourceFile parts %s' % sParts )
                    replacement = None
                    previousRejects = []
                    while replacement == None and aFilename != '':
                        for i in reversed(range(len(sParts))):
                            newFn = aFolder
                            for j in range(i,len(sParts)):
                                newFn = posixpath.join( newFn,sParts[j] )
                            debugPrint( 4, '    checking %s' % newFn )
                            if os.path.exists( newFn ) and not newFn in previousRejects :
                                if YesToAll_clicked:
                                    replacement = newFn
                                    break
                                reply = QtGui.QMessageBox.question(
                                    QtGui.QApplication.activeWindow(), "%s source file not found" % obj.Name,
                                    "Unable to find\n  %s \nUse \n  %s\n instead?" % (obj.sourceFile, newFn) ,
                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.YesToAll | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
                                if reply == QtGui.QMessageBox.Yes:
                                    replacement = newFn
                                    break
                                if reply == QtGui.QMessageBox.YesToAll:
                                    replacement = newFn
                                    YesToAll_clicked = True
                                    break
                                else:
                                    previousRejects.append( newFn )
                        aFolder, aFilename = posixpath.split( aFolder )
                    if replacement != None:
                        obj.sourceFile = replacement
                    else:
                        QtGui.QMessageBox.critical(  QtGui.QApplication.activeWindow(), "Source file not found", "update of %s aborted!\nUnable to find %s" % (obj.Name, obj.sourceFile) )
                        obj.timeLastImport = 0 #force update if users repairs link
                if path_rel_to_abs( obj.sourceFile ) is not None:
                    absolutePath = path_rel_to_abs( obj.sourceFile )
                    if os.path.getmtime( absolutePath ) > obj.timeLastImport:
                        importPart( absolutePath, obj.Name,  doc_assembly )
                        solve_assembly_constraints = True
                if os.path.exists( obj.sourceFile ):
                    if os.path.getmtime( obj.sourceFile ) > obj.timeLastImport:
                        importPart( obj.sourceFile, obj.Name,  doc_assembly )
                        solve_assembly_constraints = True

        if solve_assembly_constraints:
            solveConstraints( doc_assembly )
        # constraint mirror house keeping

        for obj in doc_assembly.Objects: #for adding creating mirrored constraints in old files
            if 'ConstraintInfo' in obj.Content:
                if doc_assembly.getObject( obj.Object1 ) == None or doc_assembly.getObject( obj.Object2 ) == None:
                    debugPrint(2, 'removing %s which refers to non-existent objects' % obj.Name)
                    doc_assembly.removeObject( obj.Name ) #required for FreeCAD 0.15 which does not support the on-delete method
                if group_constraints_under_parts():
                    if not hasattr( obj.ViewObject.Proxy, 'mirror_name'):
                        if isinstance( doc_assembly.getObject( obj.Object1 ).Proxy, Proxy_importPart) \
                                or isinstance( doc_assembly.getObject( obj.Object2 ).Proxy, Proxy_importPart):
                            debugPrint(2, 'creating mirror of %s' % obj.Name)
                            doc_assembly.getObject( obj.Object2 ).touch()
                            obj.ViewObject.Proxy.mirror_name = create_constraint_mirror(  obj, obj.ViewObject.Proxy.iconPath )
            elif 'ConstraintNfo' in obj.Content: #constraint mirror
                if  doc_assembly.getObject( obj.ViewObject.Proxy.constraintObj_name ) == None:
                    debugPrint(2, 'removing %s which mirrors/links to a non-existent constraint' % obj.Name)
                    doc_assembly.removeObject( obj.Name ) #clean up for FreeCAD 0.15 which does not support the on-delete method
                elif not group_constraints_under_parts():
                     debugPrint(2, 'removing %s since group_constraints_under_parts=False' % obj.Name)
                     delattr( doc_assembly.getObject( obj.ViewObject.Proxy.constraintObj_name ),  'mirror_name' )
                     doc_assembly.removeObject( obj.Name )
            elif hasattr(obj,'Proxy') and isinstance( obj.Proxy, Proxy_importPart) and not isinstance( obj.ViewObject.Proxy, ImportedPartViewProviderProxy):
                obj.ViewObject.Proxy = ImportedPartViewProviderProxy()
                debugPrint(2, '%s.ViewObject.Proxy = ImportedPartViewProviderProxy()'%obj.Name)
        doc_assembly.recompute()


    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/importPart_update.svg',
            'MenuText': 'Update parts imported into the assembly',
            'ToolTip': 'Update parts imported into the assembly'
            }


FreeCADGui.addCommand('assembly2_updateImportedPartsCommand', UpdateImportedPartsCommand())

def duplicateImportedPart( part ):
    nameBase = part.Label
    while nameBase[-1] in '0123456789' and len(nameBase) > 0:
        nameBase = nameBase[:-1]
    try:
        newObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", findUnusedObjectName(nameBase))
    except UnicodeEncodeError:
        safeName = findUnusedObjectName('import_')
        newObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", safeName)
        newObj.Label = findUnusedLabel( nameBase )
    newObj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = part.sourceFile
    newObj.addProperty("App::PropertyFloat", "timeLastImport","importPart").timeLastImport =  part.timeLastImport
    newObj.setEditorMode("timeLastImport",1)
    newObj.addProperty("App::PropertyBool","fixedPosition","importPart").fixedPosition = False# part.fixedPosition
    newObj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = getattr(part,'updateColors',True)
    newObj.Shape = part.Shape.copy()
    for p in part.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on their role in the assembly.
        if hasattr(newObj.ViewObject, p) and p not in ['DiffuseColor','Proxy']:
            setattr(newObj.ViewObject, p, getattr( part.ViewObject, p))
    newObj.ViewObject.DiffuseColor = copy.copy( part.ViewObject.DiffuseColor )
    newObj.Proxy = Proxy_importPart()
    newObj.ViewObject.Proxy = ImportedPartViewProviderProxy()
    newObj.Placement.Base = part.Placement.Base
    newObj.Placement.Rotation = part.Placement.Rotation
    return newObj


class PartMover:
    def __init__(self, view, obj):
        self.obj = obj
        self.initialPostion = self.obj.Placement.Base
        self.copiedObject = False
        self.view = view
        self.callbackMove = self.view.addEventCallback("SoLocation2Event",self.moveMouse)
        self.callbackClick = self.view.addEventCallback("SoMouseButtonEvent",self.clickMouse)
        self.callbackKey = self.view.addEventCallback("SoKeyboardEvent",self.KeyboardEvent)
    def moveMouse(self, info):
        newPos = self.view.getPoint( *info['Position'] )
        debugPrint(5, 'new position %s' % str(newPos))
        self.obj.Placement.Base = newPos
    def removeCallbacks(self):
        self.view.removeEventCallback("SoLocation2Event",self.callbackMove)
        self.view.removeEventCallback("SoMouseButtonEvent",self.callbackClick)
        self.view.removeEventCallback("SoKeyboardEvent",self.callbackKey)
    def clickMouse(self, info):
        debugPrint(4, 'clickMouse info %s' % str(info))
        if info['Button'] == 'BUTTON1' and info['State'] == 'DOWN':
            if not info['ShiftDown'] and not info['CtrlDown']:
                self.removeCallbacks()
            elif info['ShiftDown']: #copy object
                self.obj = duplicateImportedPart( self.obj )
                self.copiedObject = True
            elif info['CtrlDown']:
                azi   =  ( numpy.random.rand() - 0.5 )*numpy.pi*2
                ela   =  ( numpy.random.rand() - 0.5 )*numpy.pi
                theta =  ( numpy.random.rand() - 0.5 )*numpy.pi
                axis = azimuth_and_elevation_angles_to_axis( azi, ela )
                self.obj.Placement.Rotation.Q = quaternion( theta, *axis )

    def KeyboardEvent(self, info):
        debugPrint(4, 'KeyboardEvent info %s' % str(info))
        if info['State'] == 'UP' and info['Key'] == 'ESCAPE':
            if not self.copiedObject:
                self.obj.Placement.Base = self.initialPostion
            else:
                FreeCAD.ActiveDocument.removeObject(self.obj.Name)
            self.removeCallbacks()



class PartMoverSelectionObserver:
     def __init__(self):
         FreeCADGui.Selection.addObserver(self)
         FreeCADGui.Selection.removeSelectionGate()
     def addSelection( self, docName, objName, sub, pnt ):
         debugPrint(4,'addSelection: docName,objName,sub = %s,%s,%s' % (docName, objName, sub))
         FreeCADGui.Selection.removeObserver(self)
         obj = FreeCAD.ActiveDocument.getObject(objName)
         view = FreeCADGui.activeDocument().activeView()
         PartMover( view, obj )


class MovePartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelectionEx() if s.Document == FreeCAD.ActiveDocument ]
        if len(selection) == 1:
            PartMover(  FreeCADGui.activeDocument().activeView(), selection[0].Object )
        else:
            PartMoverSelectionObserver()

    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/Draft_Move.svg',
            'MenuText': 'move',
            'ToolTip': 'move part  ( shift+click to copy )'
            }

FreeCADGui.addCommand('assembly2_movePart', MovePartCommand())

class DuplicatePartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelectionEx() if s.Document == FreeCAD.ActiveDocument ]
        if len(selection) == 1:
            PartMover(  FreeCADGui.activeDocument().activeView(), duplicateImportedPart( selection[0].Object ) )

    def GetResources(self):
        return {
            'MenuText': 'duplicate',
            'ToolTip': 'duplicate part (hold shift for multiple)'
            }

FreeCADGui.addCommand('assembly2_duplicatePart', DuplicatePartCommand())

#copy object


class EditPartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        obj = selection[0]
        docs = FreeCAD.listDocuments().values()
        docFilenames = [ d.FileName for d in docs ]
        if not obj.sourceFile in docFilenames :
            FreeCAD.open(obj.sourceFile)
            debugPrint(2, 'Openning %s' % str(obj.sourceFile))
        else:
            name = docs[docFilenames.index(obj.sourceFile)].Name
            debugPrint(2, 'Trying to set focus on %s, not working for some reason!' % str(obj.sourceFile))
            FreeCAD.setActiveDocument( name )
            FreeCAD.ActiveDocument=FreeCAD.getDocument( name )
            FreeCADGui.ActiveDocument=FreeCADGui.getDocument( name )
    def GetResources(self):
        return {
            'MenuText': 'edit',
            }
FreeCADGui.addCommand('assembly2_editImportedPart', EditPartCommand())

class ForkPartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        obj = selection[0]
        filename, filetype = QtGui.QFileDialog.getSaveFileName(
            QtGui.QApplication.activeWindow(),
            "Specify the filename for the fork of '%s'" % obj.Label[:obj.Label.find('_import')],
            os.path.dirname(FreeCAD.ActiveDocument.FileName),
            "FreeCAD Document (*.fcstd)"
            )
        if filename == '':
            return
        if not os.path.exists(filename):
            debugPrint(2, 'copying %s -> %s' % (obj.sourceFile, filename))
            shutil.copyfile(obj.sourceFile, filename)
            obj.sourceFile = filename
            FreeCAD.open(obj.sourceFile)
        else:
            QtGui.QMessageBox.critical(  QtGui.QApplication.activeWindow(), "Bad filename", "Specify a new filename!")

    def GetResources(self):
        return {
            'MenuText': 'fork',
            }
FreeCADGui.addCommand('assembly2_forkImportedPart', ForkPartCommand())


class DeletePartsConstraints:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        #if len(selection) == 1: not required as this check is done in initGui
        part = selection[0]
        deleteList = []
        for c in FreeCAD.ActiveDocument.Objects:
            if 'ConstraintInfo' in c.Content:
                if part.Name in [ c.Object1, c.Object2 ]:
                    deleteList.append(c)
        if len(deleteList) == 0:
            QtGui.QMessageBox.information(  QtGui.QApplication.activeWindow(), "Info", 'No constraints refer to "%s"' % part.Name)
        else:
            flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.No
            msg = "Delete %s's constraint(s):\n  - %s?" % ( part.Name, '\n  - '.join( c.Name for c in deleteList))
            response = QtGui.QMessageBox.critical(QtGui.QApplication.activeWindow(), "Delete constraints?", msg, flags )
            if response == QtGui.QMessageBox.Yes:
                for c in deleteList:
                    removeConstraint(c)
    def GetResources(self):
        return {
            'MenuText': 'delete constraints',
            }
FreeCADGui.addCommand('assembly2_deletePartsConstraints', DeletePartsConstraints())




