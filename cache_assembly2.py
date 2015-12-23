from constraintSystems import *
import copy

class SolverCache:
    def __init__(self):
        self.inputs = []
        self.input_levels = []
        self.result = None
        self.debugMode = 0

    def retrieve( self, rootSystem, constraintObjectQue, prepare_for_record=True):
        if prepare_for_record:
            self.record_levels = []
        if self.result == None:
            return rootSystem , 0
        if rootParameters(rootSystem) != self.rootParameters:
            debugPrint(4,'cache: rootParameters(rootSystem) != self.rootParameters')
            return rootSystem, 0
        for i, c in enumerate(constraintObjectQue) :
            if i > len(self.inputs)-1:
                i = i - 1
                break
            if not self.inputs[i] == CacheInput( rootSystem.variableManager, c ):
                if self.debugMode == 1:
                    i_cache = self.inputs[i]
                    i_const = CacheInput( rootSystem.variableManager, c )
                    print( i_cache )
                    print( i_const )
                    if i_cache.constraintType != i_const.constraintType:
                        print('  constraintType not equal!')
                    elif i_cache.constraintArgs != i_const.constraintArgs:
                        print('  constraintArgspe not equal!')
                    elif  i_cache.shapeElement1 != i_const.shapeElement1:
                        print( '  shapeElement1 not equal:')
                        print( i_cache.shapeElement1)
                        print( i_const.shapeElement1)
                    elif  i_cache.shapeElement2 != i_const.shapeElement2:
                        print( '  shapeElement2 not equal:')
                        print( i_cache.shapeElement2)
                        print( i_const.shapeElement2)
                    #raw_input(' for cache.debugMode1 inputs should be equal! press enter to continue')
                    #raise RuntimeError, "for cache.debugMode1 inputs should be equal!"
                i = i -1
                break
        if i < 0:
            return rootSystem, 0
        else:
            tree = [ self.result ]
            while tree[0].parentSystem <> None:
                tree.insert(0, tree[0].parentSystem)
            new_sys = copy_constraint_system( tree[ self.input_levels[i] ] )
            assert new_sys.numberOfParentSystems() == self.input_levels[i]

            new_vM = rootSystem.variableManager
            old_vM = self.result.variableManager
            for objName in old_vM.index.keys():
                if new_vM.index.has_key( objName ):
                    i_new = new_vM.index[ objName ]
                    i_old = old_vM.index[ objName ]
                    new_vM.X[ i_new: i_new+6] = old_vM.X[ i_old: i_old+6 ]
                    #nessary to update X0 too, dont think so?
            update_variableManagers( new_sys, new_vM, set() ) 

            #use id to determin the memory location of a variable
            return new_sys, i+1

        
    def record( self, constraintSystem, constraintObjectQue, que_start):
        self.vM = constraintSystem.variableManager
        self.result = constraintSystem
        #update_variableManagers( constraintSystem, self.vM ) #ensures all system nodes point to same vM, with out this different vM will result from partially solved systems
        root = constraintSystem
        while root.parentSystem <> None:
            root = root.parentSystem
        self.rootParameters = rootParameters(root)
        self.input_levels = self.input_levels[:que_start] + self.record_levels 
        #print(self.input_levels)
        del self.inputs[que_start:]
        for c in constraintObjectQue[que_start:]:
            self.inputs.append( CacheInput(constraintSystem.variableManager, c) )

def rootParameters( sys ):
    if isinstance(sys, FixedObjectSystem):
        return ['%s.FixedObjectSystem' % sys.variableManager.doc.Name, sys.objName] + [ d.getValue() for d in sys.degreesOfFreedom ]
    else:
        raise NotImplementedError, 'RootParameters for %s not support' % sys


class CacheInput:
    def __init__(self, vM, constraint ):
        self.constraintType = constraint.Type
        if constraint.Type == 'plane':
            self.constraintArgs = ( constraint.directionConstraint, constraint.offset.Value )
        elif constraint.Type == 'angle_between_planes':
            self.constraintArgs = ( constraint.angle.Value )
        elif constraint.Type == 'axial':
            self.constraintArgs = ( constraint.directionConstraint, constraint.lockRotation )
        elif constraint.Type == 'circularEdge':
            self.constraintArgs = ( constraint.directionConstraint, constraint.offset.Value, constraint.lockRotation )
        elif  constraint.Type == 'sphericalSurface':
            self.constraintArgs = ()
        else:
            raise NotImplementedError, "CacheInput for constraint type %s not supported yet"  %  constraint.Type 
        self.shapeElement1 = ShapeElementInfo(vM, constraint.Object1, constraint.SubElement1)
        self.shapeElement2 = ShapeElementInfo(vM, constraint.Object2, constraint.SubElement2)
    def __eq__(self, b):
        return self.constraintType == b.constraintType and self.constraintArgs == b.constraintArgs and self.shapeElement1 == b.shapeElement1 and self.shapeElement2 == b.shapeElement2
    def __repr__(self):
        return '<CacheInput %s constraint, constraint args %s, shapeElement1 %s, shapeElement2 %s>' % (self.constraintType, self.constraintArgs, self.shapeElement1, self.shapeElement2 )
    
class ShapeElementInfo:
    def __init__(self, vM, objName, elementName):
        self.objName = objName
        obj = vM.doc.getObject( objName )
        self.category = classifySubElement( obj, elementName )
        self.pos =  vM.rotateAndMoveUndo( objName, getSubElementPos( obj, elementName ), vM.X0 )
        if self.category in ['plane','cylindricalSurface','circularEdge','linearEdge']:
            self.axis =  vM.rotateUndo( objName, getSubElementAxis( obj, elementName ), vM.X0 )
    def __eq__(self, b, tol = 10 **-5):
        if self.objName != b.objName:
            return False
        if self.category != b.category:
            return False
        if norm( self.pos - b.pos ) >= tol:
            #print( norm( self.pos - b.pos ) )
            return False
        if hasattr(self,'axis'):
            #print( dot( self.axis, b.axis ) )
            return dot( self.axis, b.axis ) >= 1 - tol
        else:
            return True
    def __str__(self):
        return '<ShapeElementInfo %s, category %s, pos %s, axis %s>' % (self.objName, self.category, self.pos, getattr(self,'axis',None))



#copied and pasted from importPart
class _SelectionWrapper:
    'as to interface with assembly2lib classification functions'
    def __init__(self, obj, subElementName):
        assert obj != None
        self.Object = obj
        self.SubElementNames = [subElementName]
def classifySubElement(  obj, subElementName ):
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
#/copy

def copy_constraint_system( sys ):
    #preparing for copy
    doc = sys.variableManager.doc 
    del sys.variableManager.doc #FreeCAD documents cannot be copied
    sys.childSystem = None
    tree = [ sys ]
    while tree[0].parentSystem <> None:
        tree.insert(0, tree[0].parentSystem)
    constraint_objects = []
    for node in tree:
        if hasattr( node, 'constraintObj'):
            constraint_objects.append( node.constraintObj )
            del node.constraintObj #FreeCAD Objects cannot be copied
        else:
            constraint_objects.append( None )
    #/preparing to copy
    try:
        new_sys = copy.deepcopy( sys)
    except RuntimeError, msg:
        debugPrint(1, '******** cache copy error: %s' % msg)
        debugPrint(1,'trying to determine were the object causing the crash is')
        for node in tree:
            for attr_name in node.__dict__.keys():
                attr =  getattr(node,attr_name)
                if str( type( attr ) ) == "<type 'FeaturePython'>":
                    debugPrint(1,"  %s.%s is <type 'FeaturePython'>" % (node,attr_name))
                if str(type(attr)) == "<type 'App.Document'>":
                    debugPrint(1,"  %s.%s is <type 'App.Document'>" % (node,attr_name))
                if hasattr(attr,'__dict__'):
                    for sub_attr_name in attr.__dict__.keys():
                        sub_attr =  getattr(attr,sub_attr_name)
                        if str( type( sub_attr ) ) == "<type 'FeaturePython'>":
                            debugPrint(1,"  %s.%s.%s is <type 'FeaturePython'>" % (node, attr_name, sub_attr_name ))
                        if str( type( sub_attr ) ) == "<type 'App.Document'>":
                            debugPrint(1,"  %s.%s.%s is <type 'App.Document'>" % (node, attr_name, sub_attr_name ))
        raise NotImplementedError
    #readding removed objects to both sys and new sys
    sys.variableManager.doc = doc
    new_sys.variableManager.doc = doc
    for node, cObj in zip(tree, constraint_objects):
        if cObj != None:
            node.constraintObj = cObj
    new_tree = [new_sys]
    while new_tree[0].parentSystem <> None:
        new_tree.insert(0, new_tree[0].parentSystem)
    for node, cObj in zip(new_tree, constraint_objects):
        if cObj != None:
            node.constraintObj = cObj
    return new_sys

def update_variableManagers( obj, new_vM, history ): #vanurable to circular references ...
    history.add( id(obj) )
    if hasattr(obj, 'variableManager'):
        #debugPrint(4, '  %s.variableManager set to new vM' % str(obj) )
        obj.variableManager = new_vM
    for attr_name in obj.__dict__.keys():
        attr =  getattr(obj, attr_name)
        if hasattr(attr,'variableManager') and not id(attr) in history:
            update_variableManagers( attr, new_vM, history )
    if hasattr( obj, 'degreesOfFreedom'):
        for d in obj.degreesOfFreedom:
            if not id(d) in history:
                try:
                    d.migrate_to_new_variableManager( new_vM )
                except AttributeError,msg:
                    raise NotImplementedError,"%s.migrate_to_new_variableManager" % d
                history.add( id(d) )


defaultCache = SolverCache()
