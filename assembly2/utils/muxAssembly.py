from assembly2.core import *
import Part
import os, numpy

class Proxy_muxAssemblyObj:
    def execute(self, shape):
        pass

def muxObjects(doc, mode=0):
    'combines all the imported shape object in doc into one shape'
    faces = []

    if mode == 1:
        objects = doc.getSelection()
    else:
        objects = doc.Objects

    for obj in objects:
        if 'importPart' in obj.Content:
            debugPrint(3, '  - parsing "%s"' % (obj.Name))
            if hasattr(obj, 'Shape'):
                faces = faces + obj.Shape.Faces
    return Part.makeShell(faces)

def muxMapColors(doc, muxedObj, mode=0):
    'call after muxedObj.Shape =  muxObjects(doc)'
    diffuseColors = []
    faceMap = {}

    if mode == 1:
        objects = doc.getSelection()
    else:
        objects = doc.Objects

    for obj in objects:
        if 'importPart' in obj.Content and hasattr(obj, 'Shape'):
            for i, face in enumerate(obj.Shape.Faces):
                if i < len(obj.ViewObject.DiffuseColor):
                    clr = obj.ViewObject.DiffuseColor[i]
                else:
                    clr = obj.ViewObject.DiffuseColor[0]
                faceMap[faceMapKey(face)] = clr
    for f in muxedObj.Shape.Faces:
        try:
            key = faceMapKey(f)
            clr = faceMap[key]
            del faceMap[key]
        except KeyError:
            debugPrint(3, 'muxMapColors: waring no faceMap entry for %s - key %s' % (f,faceMapKey(f)))
            clr = muxedObj.ViewObject.ShapeColor
        diffuseColors.append( clr )
    muxedObj.ViewObject.DiffuseColor = diffuseColors

def faceMapKey(face):
    c = sum([ [ v.Point.x, v.Point.y, v.Point.z] for v in face.Vertexes ], [])
    return tuple(c)

def createMuxedAssembly(name=None):
        partName='muxedAssembly'
        if name!=None:
            partName = name
        debugPrint(2, 'creating assembly mux "%s"' % (partName))
        muxedObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
        muxedObj.Proxy = Proxy_muxAssemblyObj()
        muxedObj.ViewObject.Proxy = 0
        muxedObj.addProperty("App::PropertyString","type")
        muxedObj.type = 'muxedAssembly'
        muxedObj.addProperty("App::PropertyBool","ReadOnly")
        muxedObj.ReadOnly = False
        FreeCADGui.ActiveDocument.getObject(muxedObj.Name).Visibility = False
        muxedObj.addProperty("App::PropertyStringList","muxedObjectList")
        tmplist=[]
        for objlst in FreeCADGui.Selection.getSelection():
            if 'importPart' in objlst.Content:
                 tmplist.append(objlst.Name)
        muxedObj.muxedObjectList=tmplist
        if len(tmplist)>0:
            #there are objects selected, mux them
            muxedObj.Shape = muxObjects(FreeCADGui.Selection, 1)
            muxMapColors(FreeCADGui.Selection, muxedObj, 1)
        else:
            #mux all objects (original behavior) 
            for objlst in FreeCAD.ActiveDocument.Objects:
                if 'importPart' in objlst.Content:
                    tmplist.append(objlst.Name)
            muxedObj.muxedObjectList=tmplist
            if len(tmplist)>0:
                muxedObj.Shape = muxObjects(FreeCAD.ActiveDocument, 0)
                muxMapColors(FreeCAD.ActiveDocument, muxedObj, 0)
            else:
                debugPrint(2, 'Nothing to Mux')


   
class MuxAssemblyCommand:
    def Activated(self):
        #we have to handle the mux name here
        createMuxedAssembly()
        FreeCAD.ActiveDocument.recompute()

       
    def GetResources(self):
        msg = 'Combine all parts into a single object \n\
or combine all selected parts into a single object\n(for example to create a drawing of the whole or part of the assembly)'
        return {
            'Pixmap' : ':/assembly2/icons/muxAssembly.svg',
            'MenuText': msg,
            'ToolTip': msg
            }

class MuxAssemblyRefreshCommand:
    def Activated(self):
        
        #first list all muxes in active document
        allMuxesList=[]
        for objlst in FreeCAD.ActiveDocument.Objects:
            if hasattr(objlst,'type'):
                if 'muxedAssembly' in objlst.type:
                    if objlst.ReadOnly==False:
                        allMuxesList.append(objlst.Name)
        #Second, create a list of selected objects and check if there is a mux
        allSelMuxesList=[]
        for objlst in FreeCADGui.Selection.getSelection():
            tmpobj = FreeCAD.ActiveDocument.getObject(objlst.Name)
            if 'muxedAssembly' in tmpobj.type:
                if tmpobj.ReadOnly==False:
                    allSelMuxesList.append(objlst.Name)
        refreshMuxesList=[]
        if len(allSelMuxesList) > 0 :
            refreshMuxesList=allSelMuxesList
            debugPrint(2, 'there are %d muxes in selected objects' % len(allSelMuxesList))
        else:
            if len(allMuxesList) > 0 :
                debugPrint(2, 'there are %d muxes in Active Document' % len(allMuxesList))
                refreshMuxesList=allMuxesList
            #ok there are at least 1 mux to refresh, we have to retrieve the object list for each mux 
        if len(refreshMuxesList)>0:
            FreeCADGui.Selection.clearSelection()
            for muxesobj in refreshMuxesList:
                for newselobjs in FreeCAD.ActiveDocument.getObject(muxesobj).muxedObjectList:
                    FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(newselobjs))
                tmpstr=FreeCAD.ActiveDocument.getObject(muxesobj).Label
                FreeCAD.ActiveDocument.removeObject(muxesobj)
                debugPrint(2, 'Refreshing Assembly Mux '+muxesobj)
                createMuxedAssembly(tmpstr)
                
        else:        
            debugPrint(2, 'there are no muxes in Active Document' )
        FreeCADGui.Selection.clearSelection()
        FreeCAD.ActiveDocument.recompute()
        

    def GetResources(self):
        msg = 'Refresh all muxedAssembly\n\
or refresh all selected muxedAssembly\n\
use the ReadOnly property to avoid accidental refresh'
        return {
            'Pixmap' : ':/assembly2/icons/muxAssemblyRefresh.svg',
            'MenuText': msg,
            'ToolTip': msg
        }
            
            
            
FreeCADGui.addCommand('assembly2_muxAssembly', MuxAssemblyCommand())
FreeCADGui.addCommand('assembly2_muxAssemblyRefresh', MuxAssemblyRefreshCommand())


