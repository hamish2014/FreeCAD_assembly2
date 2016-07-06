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


class ConstraintViewProviderProxy:
    def __init__( self, constraintObj, iconPath, createMirror=True, origLabel = '', mirrorLabel = '', extraLabel = '' ):
        self.iconPath = iconPath
        self.constraintObj_name = constraintObj.Name
        constraintObj.purgeTouched()
        if createMirror and group_constraints_under_parts():
            part1 = constraintObj.Document.getObject( constraintObj.Object1 )
            part2 = constraintObj.Document.getObject( constraintObj.Object2 )
            if hasattr( getattr(part1.ViewObject,'Proxy',None),'claimChildren') \
               or hasattr( getattr(part2.ViewObject,'Proxy',None),'claimChildren'):
                self.mirror_name = create_constraint_mirror(  constraintObj, iconPath, origLabel, mirrorLabel, extraLabel )
        
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
        if not allow_deletetion_when_activice_doc_ne_object_doc() and FreeCAD.activeDocument() != viewObject.Object.Document:
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


def create_constraint_mirror( constraintObj, iconPath, origLabel= '', mirrorLabel='', extraLabel = '' ):
    #FreeCAD.Console.PrintMessage("creating constraint mirror\n")
    cName = constraintObj.Name + '_mirror'
    cMirror =  constraintObj.Document.addObject("App::FeaturePython", cName)
    if origLabel == '':
        cMirror.Label = constraintObj.Label + '_'
    else:
        cMirror.Label = constraintObj.Label + '__' + mirrorLabel
        constraintObj.Label = constraintObj.Label + '__' + origLabel
        if extraLabel != '':
             cMirror.Label += '__' + extraLabel
             constraintObj.Label += '__' + extraLabel
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
        self.constraintObj_name = constraintObj.Name
        constraintObj.Proxy.mirror_name = obj.Name
        self.disable_onChanged = False
        obj.Proxy = self
        
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
                try:
                    if getattr(constraintObj, prop) != getattr( obj, prop):
                        setattr( constraintObj, prop, getattr( obj, prop) )
                except AttributeError, msg:
                    pass #loading issues...

def repair_tree_view():
    from PySide import QtGui
    doc = FreeCAD.ActiveDocument
    matches = []
    def search_children_recursively( node ):
        for c in node.children():
            if isinstance(c,QtGui.QTreeView) and isinstance(c, QtGui.QTreeWidget):
                matches.append(c)
            search_children_recursively( c)
    search_children_recursively(QtGui.qApp.activeWindow())
    for m in matches:
        tree_nodes =  get_treeview_nodes(m) 
        def get_node_by_label( label ):
            if tree_nodes.has_key( label ) and len( tree_nodes[label] ) == 1:
                return tree_nodes[label][0]
            elif not tree_nodes.has_key( obj.Label ):
                FreeCAD.Console.PrintWarning( "  repair_tree_view: skipping %s since no node with text(0) == %s\n" % ( label, label) )
            else:
                FreeCAD.Console.PrintWarning( "  repair_tree_view: skipping %s since multiple nodes matching label\n" % ( label, label) )
        if tree_nodes.has_key( doc.Label ):
            #FreeCAD.Console.PrintMessage( tree_nodes )
            for imported_obj in doc.Objects:
                if isinstance( imported_obj.ViewObject.Proxy, ImportedPartViewProviderProxy ):
                    if get_node_by_label( imported_obj.Label ):
                        node_imported_obj =  get_node_by_label( imported_obj.Label )
                        for constraint_obj in imported_obj.ViewObject.Proxy.claimChildren():
                            if get_node_by_label( constraint_obj.Label ):
                                node_constraint_obj = get_node_by_label( constraint_obj.Label )
                                if id( node_constraint_obj.parent()) != id(node_imported_obj):
                                    FreeCAD.Console.PrintMessage("repair_tree_view: %s under %s and not %s, repairing\n" % (constraint_obj.Label, node_constraint_obj.parent().text(0),  imported_obj.Label ))
                                    wrong_parent = node_constraint_obj.parent()
                                    wrong_parent.removeChild( node_constraint_obj )
                                    node_imported_obj.addChild( node_constraint_obj )
            #break

def get_treeview_nodes( treeWidget ):
    from PySide import QtGui
    tree_nodes = {}
    def walk( node ):
        key =  node.text(0)
        #print(key)
        if not tree_nodes.has_key( key ):
            tree_nodes[ key ] = []
        tree_nodes[key].append( node )
        for i in range( node.childCount() ):
            walk( node.child( i ) )
    walk( treeWidget.itemAt(0,0) )
    return tree_nodes

