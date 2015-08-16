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
    faceMap = {}
    for obj in doc.Objects:
        if 'importPart' in obj.Content:
            for face,clr in zip(obj.Shape.Faces, obj.ViewObject.DiffuseColor):
                faceMap[faceMapKey(face)] = clr    
    for f in muxedObj.Shape.Faces:
        try:
            clr = faceMap[faceMapKey(f)] 
        except KeyError:
            debugPrint(3, 'muxMapColors: waring no faceMap entry for %s - key %s' % (f,faceMapKey(f)))
            clr = muxedObj.ViewObject.ShapeColor
        diffuseColors.append( clr )
    muxedObj.ViewObject.DiffuseColor = diffuseColors

def faceMapKey(face):
    c = sum([ [v.Point.x, v.Point.y, v.Point.z] for v in face.Vertexes ], [])
    return tuple(c)
    
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
            FreeCADGui.ActiveDocument.getObject(muxedObj.Name).Visibility = False
        else:
            muxedObj = checkResult[0]
            debugPrint(2, 'updating assembly mux "%s"' % (muxedObj.Name))
        muxedObj.Shape = muxObjects( FreeCAD.ActiveDocument )
        muxMapColors(FreeCAD.ActiveDocument, muxedObj)
        FreeCAD.ActiveDocument.recompute()

       
    def GetResources(self): 
        msg = 'Combine assembly into a single object ( use to create a drawing of the assembly, and so on...)'
        return {
            'Pixmap' : os.path.join( __dir__ , 'muxAssembly.svg' ) , 
            'MenuText': msg, 
            'ToolTip': msg
            } 

FreeCADGui.addCommand('muxAssembly', MuxAssemblyCommand())
