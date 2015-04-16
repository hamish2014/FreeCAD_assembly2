'''
Used for importing parts from other FreeCAD documents.
When update parts is executed, this library import or updates the parts in the assembly document.
'''
from assembly2lib import *
from assembly2lib import __dir__
from PySide import QtGui
import os, numpy, shutil
from lib3D import *

def importPart( filename, partName=None ):
    updateExistingPart = partName <> None
    if updateExistingPart:
        FreeCAD.Console.PrintMessage("updating part %s from %s\n" % (partName,filename))
    else:
        FreeCAD.Console.PrintMessage("importing part from %s\n" % filename)
        
    doc_already_open = filename in [ d.FileName for d in FreeCAD.listDocuments().values() ] 
    debugPrint(4, "%s open already %s" % (filename, doc_already_open))
    if not doc_already_open:
        currentDoc = FreeCAD.ActiveDocument.Name
        FreeCAD.open(filename)
        FreeCAD.setActiveDocument(currentDoc)
    doc = [ d for d in FreeCAD.listDocuments().values()
            if d.FileName == filename][0]
    debugPrint(3, '%s objects %s' % (doc.Name, doc.Objects))
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
        return
    obj_to_copy = visibleObjects[0]
    if updateExistingPart:
        obj = FreeCAD.ActiveDocument.getObject(partName)
        prevPlacement = obj.Placement
        importUpdateConstraintSubobjects( FreeCAD.ActiveDocument, obj, obj_to_copy )
    else:
        partName = findUnusedObjectName( doc.Label + '_import' )
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
        obj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = filename
        obj.addProperty("App::PropertyFloat", "timeLastImport","importPart")
        obj.setEditorMode("timeLastImport",1)  
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
    obj.timeLastImport = os.path.getmtime( obj.sourceFile )
    if not doc_already_open: #then close again
        FreeCAD.closeDocument(doc.Name)
        FreeCAD.setActiveDocument(currentDoc)
    return obj

class Proxy_importPart:
    def execute(self, shape):
        pass

class ImportPartCommand:
    def Activated(self):
        view = FreeCADGui.activeDocument().activeView()
        filename, filetype = QtGui.QFileDialog.getOpenFileName( 
            QtGui.qApp.activeWindow(),
            "Select FreeCAD document to import part from",
            os.path.dirname(FreeCAD.ActiveDocument.FileName),
            "FreeCAD Document (*.fcstd)"
            )
        if filename == '':
            return
        importedObject = importPart( filename )
        FreeCAD.ActiveDocument.recompute()
        if not importedObject.fixedPosition: #will be true for the first imported part 
            PartMover( view, importedObject )
        else:
            from PySide import QtCore
            self.timer = QtCore.QTimer()
            QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.GuiViewFit)
            self.timer.start( 500 ) #0.5 seconds

    def GuiViewFit(self):
        FreeCADGui.SendMsgToActiveView("ViewFit") #dont know why this does not work
        self.timer.stop()
       
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
                if not hasattr( obj, 'timeLastImport'):
                    obj.addProperty("App::PropertyFloat", "timeLastImport","importPart") #should default to zero which will force update.
                    obj.setEditorMode("timeLastImport",1)  
                if not os.path.exists( obj.sourceFile ):
                    QtGui.QMessageBox.critical(  QtGui.qApp.activeWindow(), "Source file not found", "update of %s aborted due source file being missing..." % obj.Name )
                    obj.timeLastImport = 0 #force update if users repairs link
                elif os.path.getmtime( obj.sourceFile ) > obj.timeLastImport:
                    importPart( obj.sourceFile, obj.Name )
        FreeCAD.ActiveDocument.recompute()
    def GetResources(self): 
        return {
            'Pixmap' : os.path.join( __dir__ , 'importPart_update.svg' ) , 
            'MenuText': 'Update parts imported into the assembly', 
            'ToolTip': 'Update parts imported into the assembly'
            } 
FreeCADGui.addCommand('updateImportedPartsCommand', UpdateImportedPartsCommand())


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
                partName = findUnusedObjectName( self.obj.Name[:self.obj.Name.find('_import') + len('_import')] )
                newObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
                newObj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = self.obj.sourceFile
                newObj.addProperty("App::PropertyFloat", "timeLastImport","importPart").timeLastImport =  self.obj.timeLastImport
                newObj.setEditorMode("timeLastImport",1)  
                newObj.addProperty("App::PropertyBool","fixedPosition","importPart").fixedPosition = self.obj.fixedPosition
                newObj.Shape = self.obj.Shape.copy()
                newObj.ViewObject.Proxy = 0
                for p in self.obj.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
                    if hasattr(newObj.ViewObject, p):
                        setattr(newObj.ViewObject, p, getattr(self.obj.ViewObject, p))
                newObj.Proxy = Proxy_importPart()
                newObj.Placement.Base = self.obj.Placement.Base
                newObj.Placement.Rotation = self.obj.Placement.Rotation
                self.obj = newObj
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
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 1:
            PartMover(  FreeCADGui.activeDocument().activeView(), selection[0].Object )
        else:
            PartMoverSelectionObserver()
       
    def GetResources(self): 
        return {
            'Pixmap' : os.path.join( __dir__ , 'Draft_Move.svg' ) , 
            'MenuText': 'move', 
            'ToolTip': 'move part  ( shift+click to copy )'
            } 

FreeCADGui.addCommand('assembly2_movePart', MovePartCommand())

class DuplicatePartCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 1:
            obj = selection[0].Object
            partName = findUnusedObjectName( obj.Name[:obj.Name.find('_import') + len('_import')] )
            newObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
            newObj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = obj.sourceFile
            newObj.addProperty("App::PropertyFloat", "timeLastImport","importPart").timeLastImport =  obj.timeLastImport
            newObj.setEditorMode("timeLastImport",1)  
            newObj.addProperty("App::PropertyBool","fixedPosition","importPart").fixedPosition = obj.fixedPosition
            newObj.Shape = obj.Shape.copy()
            newObj.ViewObject.Proxy = 0
            for p in obj.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
                if hasattr(newObj.ViewObject, p):
                    setattr(newObj.ViewObject, p, getattr(obj.ViewObject, p))
            newObj.Proxy = Proxy_importPart()
            newObj.Placement.Base = obj.Placement.Base
            newObj.Placement.Rotation = obj.Placement.Rotation
            PartMover(  FreeCADGui.activeDocument().activeView(), newObj )

    def GetResources(self): 
        return {
            'MenuText': 'duplicate', 
            'ToolTip': 'duplicate part (hold shift for multiple)'
            } 

FreeCADGui.addCommand('assembly2_duplicatePart', DuplicatePartCommand())
    
#copy object


class EditPartCommand:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
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
        selection = FreeCADGui.Selection.getSelection()
        obj = selection[0]
        filename, filetype = QtGui.QFileDialog.getSaveFileName( 
            QtGui.qApp.activeWindow(),
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
            QtGui.QMessageBox.critical(  QtGui.qApp.activeWindow(), "Bad filename", "Specify a new filename!")

    def GetResources(self): 
        return { 
            'MenuText': 'fork', 
            } 
FreeCADGui.addCommand('assembly2_forkImportedPart', ForkPartCommand())


class DeletePartsConstraints:
    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        if len(selection) == 1:
            part = selection[0]
            deleteList = []
            for c in FreeCAD.ActiveDocument.Objects:
                if 'ConstraintInfo' in c.Content:
                    if part.Name in [ c.Object1, c.Object2 ]:
                        deleteList.append(c)
            if len(deleteList) == 0:
                QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Info", 'No constraints refer to "%s"' % part.Name)
            else:
                flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.No
                msg = "Delete %s's constraint(s):\n  - %s?" % ( part.Name, '\n  - '.join( c.Name for c in deleteList))
                response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Delete constraints?", msg, flags )
                if response == QtGui.QMessageBox.Yes:
                    for c in deleteList:
                        FreeCAD.Console.PrintError("removing constraint %s" % c.Name)
                        FreeCAD.ActiveDocument.removeObject(c.Name)
    def GetResources(self): 
        return { 
            'MenuText': 'delete constraints', 
            } 
FreeCADGui.addCommand('assembly2_deletePartsConstraints', DeletePartsConstraints())





from variableManager import ReversePlacementTransformWithBoundsNormalization

class _SelectionWrapper:
    'as to interface with assembly2lib classification functions'
    def __init__(self, obj, subElementName):
        self.Object = obj
        self.SubElementNames = [subElementName]
        

def classifySubElement( obj, subElementName ):
    selection = _SelectionWrapper( obj, subElementName )
    if planeSelected( selection ):
        return 'plane'
    elif cylindricalPlaneSelected( selection ):
        return 'cylindricalSurface'
    elif CircularEdgeSelected( selection ):
        return 'circularEdge'
    elif LinearEdgeSelected( selection ):
        return 'linearEdge'
    elif vertexSelected( selection ):
        return 'vertex' #all vertex belong to Vertex classification
    elif sphericalSurfaceSelected( selection ):
        return 'sphericalSurface'
    else:
        return 'other'

def classifySubElements( obj ):
    C = { 
        'plane': [],
        'cylindricalSurface': [],
        'circularEdge':[],
        'linearEdge':[], 
        'vertex':[], 
        'sphericalSurface':[],
        'other':[] 
        }
    prefixDict = {'Vertexes':'Vertex','Edges':'Edge','Faces':'Face'}
    for listName in ['Vertexes','Edges','Faces']:
        for j, subelement in enumerate( getattr( obj.Shape, listName) ):
            subElementName = '%s%i' % (prefixDict[listName], j+1 )
            catergory = classifySubElement( obj, subElementName )
            C[catergory].append(subElementName)
    return C
    
class SubElementDifference:
    def __init__(self, obj1, SE1, T1, obj2, SE2, T2):
        self.obj1 = obj1
        self.SE1 = SE1
        self.T1 = T1
        self.obj2 = obj2
        self.SE2 = SE2
        self.T2 = T2
        self.catergory = classifySubElement( obj1, SE1 )
        self.error1 = 0 #not used for 'vertex','sphericalSurface','other'
        if self.catergory == 'circularEdge':
            v1 = self.getAxis( obj1, SE1 )
            v2 = self.getAxis( obj2, SE2 )
            self.error1 = 1 - dot( T1.unRotate(v1), T2.unRotate(v2) )
        if self.catergory <> 'other':
            p1 = self.getPos( obj1, SE1 )
            p2 = self.getPos( obj2, SE2 )
            self.error2 = norm( T1(p1) - T2(p2) )
        else:
            self.error2 = 1 - (SE1 == SE2) #subelements have the same name

    def getAxis(self, obj, subElement):
        'copied from constraintSystems getAxis'
        if subElement.startswith('Face'):
            axis = getObjectFaceFromName(obj, subElement).Surface.Axis
        elif subElement.startswith('Edge'):
            edge = getObjectEdgeFromName(obj, subElement)
            if isinstance(edge.Curve, Part.Line):
                axis = edge.Curve.tangent(0)[0]
            else: #circular curve
                axis =  edge.Curve.Axis
        if axis <> None:
            return numpy.array(axis)
        else:
            raise NotImplementedError,"subElement %s" % subElement
    def getPos(self, obj, subElement):
        pos = None
        if subElement.startswith('Face'):
            surface = getObjectFaceFromName(obj, subElement).Surface
            if str(surface) == '<Plane object>':
                pos = surface.Position
            elif all( hasattr(surface,a) for a in ['Axis','Center','Radius'] ):
                pos = surface.Center
            else:
                raise NotImplementedError,"getPos %s" % str(surface)
        elif subElement.startswith('Edge'):
            edge = getObjectEdgeFromName(obj, subElement)
            if isinstance(edge.Curve, Part.Line):
                pos = edge.Curve.StartPoint
            else: #circular curve
                pos = edge.Curve.Center    
        elif subElement.startswith('Vertex'):
            return  getObjectVertexFromName(obj, subElement).Point
        if pos <> None:
            return numpy.array(pos)
        else:
            raise NotImplementedError,"subElement %s" % subElement
        
    def __lt__(self, b):
        if self.error1 <> b.error1:
            return self.error1 < b.error1
        else:
            return self.error2 < b.error2
    def __str__(self):
        return '<SubElementDifference:%s SE1:%s SE2:%s error1: %f error2: %f>' % ( self.catergory, self.SE1, self.SE2, self.error1, self.error2 )


def importUpdateConstraintSubobjects( doc, oldObject, newObject ):
    #classify subelements
    debugPrint(2,'Import: Updating Constraint SubElements Names')
    newObjSubElements = classifySubElements( newObject )
    debugPrint(3,'newObjSubElements: %s' % newObjSubElements)
    # generating transforms
    T_old = ReversePlacementTransformWithBoundsNormalization( oldObject )
    T_new = ReversePlacementTransformWithBoundsNormalization( newObject )
    partName = oldObject.Name
    #generating mappings

    mappings = {}
    #vertexs
    #Q = [ Tnew(v,Point) for v in newObject.Vertexes ]
    #for i,vOld in enumerate(oldObject.Shape.Vertexes):
    #    p = T_old(vOld.Point)
    #    d = [ [norm(p-q),j] for j,q in enumerate(Q) ]
    #    d_min = min(d)
    #    mappings['Vertex%i']
    #    for j,vNew in enumerate(newObject.Shape.Vertexes):
            

    vertexs_old = numpy.array([ T_old(v.Point) for v in oldObject.Shape.Vertexes ])
    vertexs_new = numpy.array([ T_new(v.Point) for v in newObject.Shape.Vertexes ])

    
    for c in doc.Objects:
        if 'ConstraintInfo' in c.Content:
            if partName == c.Object1:
                SubElement = "SubElement1"
            elif partName == c.Object2:
                SubElement = "SubElement2"
            else:
                SubElement = None
            if SubElement: #same as subElement <> None
                subElementName = getattr(c, SubElement)
                debugPrint(3,'  updating %s.%s' % (c.Name, SubElement))
                catergory = classifySubElement( oldObject, subElementName )
                D = [ SubElementDifference( oldObject, subElementName, T_old, newObject, SE2, T_new)
                      for SE2 in newObjSubElements[catergory] ]
                #for d in D:
                #    debugPrint(2,'      %s' % d)
                d_min = min(D)
                debugPrint(3,'    closest match %s' % d_min)
                newSE =  d_min.SE2
                debugPrint(2,'  updating %s.%s   %s->%s' % (c.Name, SubElement, subElementName, newSE))
                setattr(c, SubElement, newSE) 
