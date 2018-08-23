import FreeCAD, FreeCADGui
from pivy import coin
import traceback

def group_constraints_under_parts():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('groupConstraintsUnderParts', True)

def allow_deletetion_when_activice_doc_ne_object_doc():
    parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return parms.GetBool('allowDeletetionFromExternalDocuments', False)


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
        from objectProxy import ConstraintMirrorObjectProxy
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
    from objectProxy import ConstraintMirrorObjectProxy
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


def repair_tree_view():
    from PySide import QtGui
    doc = FreeCAD.ActiveDocument
    matches = []
    def search_children_recursively( node ):
        for c in node.children():
            if isinstance(c,QtGui.QTreeView) and isinstance(c, QtGui.QTreeWidget):
                matches.append(c)
            search_children_recursively( c)
    search_children_recursively(QtGui.QApplication.activeWindow())
    for m in matches:
        tree_nodes =  get_treeview_nodes(m)
        def get_node_by_label( label ):
            if label in tree_nodes and len( tree_nodes[label] ) == 1:
                return tree_nodes[label][0]
            elif not obj.Label in tree_nodes:
                FreeCAD.Console.PrintWarning( "  repair_tree_view: skipping %s since no node with text(0) == %s\n" % ( label, label) )
            else:
                FreeCAD.Console.PrintWarning( "  repair_tree_view: skipping %s since multiple nodes matching label\n" % ( label, label) )
        if doc.Label in tree_nodes: #all the code up until now has geen to find the QtGui.QTreeView widget (except for the get_node_by_label function)
            #FreeCAD.Console.PrintMessage( tree_nodes )
            for imported_obj in doc.Objects:
                try: #allow use of assembly2 contraints also on non imported objects
                    if isinstance( imported_obj.ViewObject.Proxy, ImportedPartViewProviderProxy ):
                        #FreeCAD.Console.PrintMessage( 'checking claim children for %s\n' % imported_obj.Label )
                        if get_node_by_label( imported_obj.Label ):
                            node_imported_obj =  get_node_by_label( imported_obj.Label )
                            if not hasattr( imported_obj.ViewObject.Proxy, 'Object'):
                                imported_obj.ViewObject.Proxy.Object = imported_obj # proxy.attach not called properly
                                FreeCAD.Console.PrintMessage('repair_tree_view: %s.ViewObject.Proxy.Object = %s' % (imported_obj.Name, imported_obj.Name) )
                            for constraint_obj in imported_obj.ViewObject.Proxy.claimChildren():
                                #FreeCAD.Console.PrintMessage('  - %s\n' % constraint_obj.Label )
                                if get_node_by_label( constraint_obj.Label ):
                                    #FreeCAD.Console.PrintMessage('     (found treeview node)\n')
                                    node_constraint_obj = get_node_by_label( constraint_obj.Label )
                                    if id( node_constraint_obj.parent()) != id(node_imported_obj):
                                        FreeCAD.Console.PrintMessage("repair_tree_view: %s under %s and not %s, repairing\n" % (constraint_obj.Label, node_constraint_obj.parent().text(0),  imported_obj.Label ))
                                        wrong_parent = node_constraint_obj.parent()
                                        wrong_parent.removeChild( node_constraint_obj )
                                        node_imported_obj.addChild( node_constraint_obj )
                except:
                    # FreeCAD.Console.PrintWarning( "not repaired %s \n" % ( imported_obj.Label ) )
                    pass
            #break

def get_treeview_nodes( treeWidget ):
    from PySide import QtGui
    tree_nodes = {}
    def walk( node ):
        key =  node.text(0)
        #print(key)
        if not key in tree_nodes:
            tree_nodes[ key ] = []
        tree_nodes[key].append( node )
        for i in range( node.childCount() ):
            walk( node.child( i ) )
    walk( treeWidget.itemAt(0,0) )
    return tree_nodes
