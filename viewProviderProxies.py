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
                if hasattr( c.Proxy, 'mirrorName'): # then also deleter constraints mirror 
                    doc.removeObject( c.Proxy.mirrorName )
                doc.removeObject(c.Name)
        return True # If False is returned the object won't be deleted

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def attach(self, vobj):
        self.object_Name = vobj.Object.Name
        #self.ViewObject = vobj
        self.Object = vobj.Object

    def claimChildren(self):
        '''
        loading notes:
        if isinstance( getattr(obj.ViewObject, 'Proxy'):
            ...
        elif elif isinstance( getattr(obj.ViewObject, 'Proxy'), ConstraintViewProviderProxy):
            ...
        check did not work.

        theory, FreeCAD loading in the follow order
        -> load stripped objects
        -> set object properties
        -> loads stripped proxies (and calls proxies methods, such as claim children)
        -> set proxies properties

        or something like that ...
        '''

        
        children = []
        if hasattr(self, 'Object'):
            importedPart = self.Object
        else:
            return None
        #if hasattr(self, 'object_Name'):
        #    importedPart = FreeCAD.ActiveDocument.getObject( self.object_Name )
        #    if importedPart == None:
        #        return []
        #else:
        #    return []
        for obj in importedPart.Document.Objects:
            if hasattr( obj, 'ViewObject'):
                if 'ConstraintNfo' in obj.Content: #constraint mirror
                    if obj.Object2 == importedPart.Name:
                        children.append( obj )
                elif 'ConstraintInfo' in obj.Content: #constraint original
                    #if hasattr(obj.ViewObject.Proxy, 'mirrorName'): #wont work as obj.ViewObject.Proxy still being loaded
                    if obj.Object1 == importedPart.Name:
                        children.append( obj )
        return children
    

class ConstraintViewProviderProxy:
    def __init__( self, constraintObj, iconPath, createMirror=True ):
        self.iconPath = iconPath
        self.constraintObj_name = constraintObj.Name
        constraintObj.purgeTouched()
        if createMirror:
            self.mirror_name = create_constraint_mirror(  constraintObj, iconPath )
        
    def getIcon(self):
        return self.iconPath
        
    def attach(self, vobj): #attach to what document?
        vobj.addDisplayMode( coin.SoGroup(),"Standard" )

    def getDisplayModes(self,obj):
        "'''Return a list of display modes.'''"
        return ["Standard"]

    def getDefaultDisplayMode(self):
        "'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
        return "Standard"

    def onDelete(self, viewObject, subelements): # subelements is a tuple of strings
        'does not seem to be called when an object is deleted pythonatically'
        parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if not parms.GetBool('allowDeletetionFromExternalDocuments', False):
            if FreeCAD.activeDocument() != viewObject.Object.Document:
                FreeCAD.Console.PrintMessage("preventing deletetion of %s since active document != %s. Disable behavior in assembly2 preferences.\n" % (viewObject.Object.Label, viewObject.Object.Document.Name) )
                return False
                #add code to delete constraint mirrors, or original
        obj = viewObject.Object
        doc = obj.Document
        if isinstance( obj.Proxy, ConstraintMirrorObjectProxy ):
            doc.removeObject(  obj.Proxy.constraintObj_name ) # also delete the original constraint which obj mirrors
        elif hasattr( obj.Proxy, 'mirror_name'): # the original constraint, #isinstance( obj.Proxy,  ConstraintObjectProxy ) not done since ConstraintObjectProxy not defined in namespace 
            doc.removeObject( obj.Proxy.mirror_name ) # also delete mirror
        return True


class ConstraintMirrorViewProviderProxy( ConstraintViewProviderProxy ):
    def __init__( self, constraintObj, iconPath ):
        self.iconPath = iconPath
        self.constraintObj_name = constraintObj.Name
    def attach(self, vobj):
        vobj.addDisplayMode( coin.SoGroup(),"Standard" )


def create_constraint_mirror( constraintObj, iconPath ):
    #FreeCAD.Console.PrintMessage("creating constraint mirror\n")
    cName = constraintObj.Name + '_mirror'
    cMirror =  constraintObj.Document.addObject("App::FeaturePython", cName)
    cMirror.Label = constraintObj.Label + '_'
    for pName in constraintObj.PropertiesList:
        if constraintObj.getGroupOfProperty( pName ) == 'ConstraintInfo':
            #if constraintObj.getTypeIdOfProperty( pName ) == 'App::PropertyEnumeration':
            #    continue #App::Enumeration::contains(const char*) const: Assertion `_EnumArray' failed.
            cMirror.addProperty(
                constraintObj.getTypeIdOfProperty( pName ),
                pName,
                "ConstraintNfo" #instead of ConstraintInfo, as to not confuse the assembly2sovler
                )
            if pName == 'directionConstraint':
                v =  constraintObj.directionConstraint
                if v != "none": #then updating a document with mirrors
                    cMirror.directionConstraint =  ["aligned","opposed"]
                    cMirror.directionConstraint = v
                else:
                    cMirror.directionConstraint =  ["none","aligned","opposed"]
            else:
                setattr( cMirror, pName, getattr( constraintObj, pName) )
            if constraintObj.getEditorMode(pName) == ['ReadOnly']:
                cMirror.setEditorMode( pName, 1 )
    ConstraintMirrorObjectProxy( cMirror, constraintObj )
    cMirror.ViewObject.Proxy = ConstraintMirrorViewProviderProxy( constraintObj, iconPath )
    #cMirror.purgeTouched()
    return cMirror.Name

class ConstraintMirrorObjectProxy:
    def __init__(self, obj, constraintObj ):
        obj.Proxy = self
        self.constraintObj_name = constraintObj.Name
        constraintObj.Proxy.mirror_name = obj.Name
        self.disable_onChanged = False
        
    def execute(self, obj):
        return #no work required in onChanged causes touched in original constraint ...

    def onChanged(self, obj, prop):
        '''
        is triggered by Python code!
        And on document loading...
        '''
        #FreeCAD.Console.PrintMessage("%s.%s property changed\n" % (obj.Name, prop))
        if getattr( self, 'disable_onChanged', True):
            return 
        if obj.getGroupOfProperty( prop ) == 'ConstraintNfo':
            if hasattr( self, 'constraintObj_name' ):
                constraintObj = obj.Document.getObject( self.constraintObj_name )
                if getattr(constraintObj, prop) != getattr( obj, prop):
                    setattr( constraintObj, prop, getattr( obj, prop) )
