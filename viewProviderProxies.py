import FreeCAD
from pivy import coin
import traceback

class ImportedPartViewProviderProxy:
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        viewObject = feature
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
