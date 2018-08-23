import FreeCAD, FreeCADGui
from pivy import coin
import traceback

def group_constraints_under_parts():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('groupConstraintsUnderParts', True)

def allow_deletetion_when_activice_doc_ne_object_doc():
    parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return parms.GetBool('allowDeletetionFromExternalDocuments', False)


class ImportedPartViewProviderProxy:
    def onDelete(self, viewObject, subelements): # subelements is a tuple of strings
        if not allow_deletetion_when_activice_doc_ne_object_doc() and FreeCAD.activeDocument() != viewObject.Object.Document:
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
            return []
        if not group_constraints_under_parts():
            return []

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

    def setupContextMenu(self, ViewObject, popup_menu):
        ''' for playing around in an iPythonConsole:
        from PySide import *
        app = QtGui.QApplication([])
        menu = QtGui.QMenu()
        '''
        #self.pop_up_menu_items = [] #worried about the garbage collector ...
        #popup_menu.addSeparator()
        #menu = popup_menu.addMenu('Assembly 2')
        #PopUpMenuItem( self, menu, 'edit', 'assembly2_editImportedPart' )
        #if self.Object.Document == FreeCAD.ActiveDocument:
        #    for label, cmd in [
        #        [ 'move', 'assembly2_movePart'],
        #        [ 'duplicate', 'assembly2_duplicatePart'],
        #        [ 'fork', 'assembly2_forkImportedPart'],
        #        [ 'delete constraints', 'assembly2_deletePartsConstraints']
        #        ]:
        #         PopUpMenuItem( self, menu, label, cmd )
        # abandoned since context menu not shown when contextMenu activated in viewer

class PopUpMenuItem:
    def __init__( self, proxy, menu, label, Freecad_cmd ):
        self.Object = proxy.Object
        self.Freecad_cmd =  Freecad_cmd
        action = menu.addAction(label)
        action.triggered.connect( self.execute )
        proxy.pop_up_menu_items.append( self )
    def execute( self ):
        try:
            FreeCADGui.runCommand( self.Freecad_cmd )
        except:
            FreeCAD.Console.PrintError( traceback.format_exc() )
