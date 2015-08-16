'''
Used for importing parts from other FreeCAD documents.
When update parts is executed, this library import or updates the parts in the assembly document.
'''
from assembly2lib import *
from assembly2lib import __dir__
import Part
import os, numpy

class Proxy_muxAssemblyObj:
    def execute(self, shape):
        pass

def muxObjects( doc ):
    'combines all the imported shape object in doc into one shape'
    faces = []
    for obj in doc.Objects:
        if 'importPart' in obj.Content:
            debugPrint(3, '  - parsing "%s"' % (obj.Name))
            faces = faces + obj.Shape.Faces
    return Part.makeShell(faces)

def muxMapColors( doc, muxedObj):
    'call after muxedObj.Shape =  muxObjects(doc)'
    diffuseColors = []
    for f1 in muxedObj.Shape.Faces:
        foundMatch = False
        for obj in doc.Objects:
            if 'importPart' in obj.Content:
                for j,f2 in enumerate(obj.Shape.Faces):
                    if not foundMatch and facesEqual(f1,f2):
                        if j < len(obj.ViewObject.DiffuseColor):
                            diffuseColors.append( obj.ViewObject.DiffuseColor[j] )
                        else:
                            diffuseColors.append( obj.ViewObject.ShapeColor )
                        foundMatch = True
                        break
            #if foundMatch:
            #    break
        if not foundMatch:
            diffuseColors.append( muxedObjViewObject.ShapeColor )
    muxedObj.ViewObject.DiffuseColor = diffuseColors

def facesEqual(f1,f2):
    return len(f1.Vertexes) == len(f2.Vertexes) \
        and f1.Area == f2.Area \
        and all( v1.Point == v2.Point for v1,v2 in zip(f1.Vertexes, f2.Vertexes) )

class MuxAssemblyCommand:
    def Activated(self):
        #first check if assembly mux part already existings
        checkResult = [ obj  for obj in FreeCAD.ActiveDocument.Objects 
                        if hasattr(obj, 'type') and obj.type == 'muxedAssembly' ]
        if len(checkResult) == 0:
            partName = 'muxedAssembly'
            debugPrint(2, 'creating assembly mux "%s"' % (partName))
            muxedObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
            muxedObj.Proxy = Proxy_muxAssemblyObj()
            muxedObj.ViewObject.Proxy = 0
            muxedObj.addProperty("App::PropertyString","type")
            muxedObj.type = 'muxedAssembly'
        else:
            muxedObj = checkResult[0]
            debugPrint(2, 'updating assembly mux "%s"' % (muxedObj.Name))
        muxedObj.Shape = muxObjects( FreeCAD.ActiveDocument )
        FreeCADGui.ActiveDocument.getObject(muxedObj.Name).Visibility = False
        FreeCAD.ActiveDocument.recompute()

       
    def GetResources(self): 
        msg = 'Combine assembly into a single object ( use to create a drawing of the assembly, and so on...)'
        return {
            'Pixmap' : os.path.join( __dir__ , 'muxAssembly.svg' ) , 
            'MenuText': msg, 
            'ToolTip': msg
            } 

FreeCADGui.addCommand('muxAssembly', MuxAssemblyCommand())
