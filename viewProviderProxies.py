import FreeCAD
from pivy import coin
import traceback

class ImportedPartViewProviderProxy:
    def onDelete(self, viewObject, subelements): # subelements is a tuple of strings
        parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if not parms.GetBool('allowDeletetionFromExternalDocuments', False):
            if FreeCAD.activeDocument() != viewObject.Object.Document:
                FreeCAD.Console.PrintMessage("preventing deletetion of %s since active document != %s. Disable behavior in assembly2 preferences.\n" % (viewObject.Object.Label, viewObject.Object.Document.Name) )
                return False
        obj = viewObject.Object
        doc = obj.Document
        #FreeCAD.Console.PrintMessage('ConstraintObjectViewProviderProxy.onDelete: removing constraints refering to %s (label:%s)\n' % (obj.Name, obj.Label))
        deleteList = []
        for c in doc.Objects:
            if 'ConstraintInfo' in c.Content:
                if obj.Name in [ c.Object1, c.Object2 ]:
                    deleteList.append(c)
        if len(deleteList) > 0:
            #FreeCAD.Console.PrintMessage("  delete list %s\n" % str(deleteList) )
            for c in deleteList:
                #FreeCAD.Console.PrintMessage("  - removing constraint %s\n" % c.Name )
                doc.removeObject(c.Name)
        return True # If False is returned the object won't be deleted

class ConstraintViewProviderProxy:
    def __init__( self, constraintObj, iconPath ):
        self.iconPath = iconPath
        self.constraintObj_name = constraintObj.Name

    def constraintObj(self):
        return FreeCAD.ActiveDocument.getObject( self.constraintObj_name )

    def getIcon(self):
        return self.iconPath
        
    def attach(self, vobj):
        #self.standard = coin.SoGroup()
        #vobj.addDisplayMode(self.standard,"Standard")
        vobj.addDisplayMode( coin.SoGroup(),"Standard" )

    def getDisplayModes(self,obj):
        "'''Return a list of display modes.'''"
        return ["Standard"]

    def getDefaultDisplayMode(self):
        "'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
        return "Standard"

    def onDelete(self, viewObject, subelements): # subelements is a tuple of strings
        parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if not parms.GetBool('allowDeletetionFromExternalDocuments', False):
            if FreeCAD.activeDocument() != viewObject.Object.Document:
                FreeCAD.Console.PrintMessage("preventing deletetion of %s since active document != %s. Disable behavior in assembly2 preferences.\n" % (viewObject.Object.Label, viewObject.Object.Document.Name) )
                return False
        return True
