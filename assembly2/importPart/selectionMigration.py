'''
When parts are updated, the shape elements naming often changes.
i.e. Edge4 -> Edge10
The constraint reference are therefore get mangled.
Below follows code to help migrate the shape references during a shape update.
'''



from assembly2.selection import *
from assembly2.lib3D import *
from assembly2.solvers.dof_reduction_solver.variableManager import ReversePlacementTransformWithBoundsNormalization

class _SelectionWrapper:
    'as to interface with assembly2lib classification functions'
    def __init__(self, obj, subElementName):
        self.Object = obj
        self.SubElementNames = [subElementName]


def classifySubElement( obj, subElementName ):
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

def classifySubElements( obj ):
    C = {
        'plane': [],
        'cylindricalSurface': [],
        'circularEdge':[],
        'linearEdge':[],
        'vertex':[],
        'sphericalSurface':[],
        'other':[]
        }
    prefixDict = {'Vertexes':'Vertex','Edges':'Edge','Faces':'Face'}
    for listName in ['Vertexes','Edges','Faces']:
        for j, subelement in enumerate( getattr( obj.Shape, listName) ):
            subElementName = '%s%i' % (prefixDict[listName], j+1 )
            catergory = classifySubElement( obj, subElementName )
            C[catergory].append(subElementName)
    return C

class SubElementDifference:
    def __init__(self, obj1, SE1, T1, obj2, SE2, T2):
        self.obj1 = obj1
        self.SE1 = SE1
        self.T1 = T1
        self.obj2 = obj2
        self.SE2 = SE2
        self.T2 = T2
        self.catergory = classifySubElement( obj1, SE1 )
        #assert self.catergory == classifySubElement( obj2, SE2 )
        self.error1 = 0 #not used for 'vertex','sphericalSurface','other'
        if self.catergory in ['cylindricalSurface','circularEdge','plane','linearEdge']:
            v1 = getSubElementAxis( obj1, SE1 )
            v2 = getSubElementAxis( obj2, SE2 )
            self.error1 = 1 - dot( T1.unRotate(v1), T2.unRotate(v2) )
        if self.catergory != 'other':
            p1 = getSubElementPos( obj1, SE1 )
            p2 = getSubElementPos( obj2, SE2 )
            self.error2 = norm( T1(p1) - T2(p2) )
        else:
            self.error2 = 1 - (SE1 == SE2) #subelements have the same name
    def __lt__(self, b):
        if self.error1 != b.error1:
            return self.error1 < b.error1
        else:
            return self.error2 < b.error2
    def __str__(self):
        return '<SubElementDifference:%s SE1:%s SE2:%s error1: %f error2: %f>' % ( self.catergory, self.SE1, self.SE2, self.error1, self.error2 )

def subElements_equal(obj1, SE1, T1, obj2, SE2, T2):
    try:
        if classifySubElement( obj1, SE1 ) == classifySubElement( obj2, SE2 ):
            diff = SubElementDifference(obj1, SE1, T1, obj2, SE2, T2)
            return diff.error1 == 0 and diff.error2 == 0
        else:
            return False
    except (IndexError, AttributeError) as e:
        return False


def importUpdateConstraintSubobjects( doc, oldObject, newObject ):
    '''
    TO DO (if time allows): add a task dialog (using FreeCADGui.Control.addDialog) as to allow the user to specify which scheme to use to update the constraint subelement names.
    '''
    #classify subelements
    if len([c for c in doc.Objects if  'ConstraintInfo' in c.Content and oldObject.Name in [c.Object1, c.Object2] ]) == 0:
        debugPrint(3,'Aborint Import Updating Constraint SubElements Names since no matching constraints')
        return
    partName = oldObject.Name
    debugPrint(2,'Import: Updating Constraint SubElements Names: "%s"' % partName)
    newObjSubElements = classifySubElements( newObject )
    debugPrint(3,'newObjSubElements: %s' % newObjSubElements)
    # generating transforms
    T_old = ReversePlacementTransformWithBoundsNormalization( oldObject )
    T_new = ReversePlacementTransformWithBoundsNormalization( newObject )
    for c in doc.Objects:
        if 'ConstraintInfo' in c.Content:
            if partName == c.Object1:
                SubElement = "SubElement1"
            elif partName == c.Object2:
                SubElement = "SubElement2"
            else:
                SubElement = None
            if SubElement: #same as subElement != None
                subElementName = getattr(c, SubElement)
                debugPrint(3,'  updating %s.%s' % (c.Name, SubElement))
                if not subElements_equal(  oldObject, subElementName, T_old, newObject, subElementName, T_new):
                    catergory = classifySubElement( oldObject, subElementName )
                    D = [ SubElementDifference( oldObject, subElementName, T_old, newObject, SE2, T_new)
                          for SE2 in newObjSubElements[catergory] ]
                    assert len(D) > 0, "%s no longer has any %ss." % ( partName, catergory)
                    #for d in D:
                    #    debugPrint(2,'      %s' % d)
                    d_min = min(D)
                    debugPrint(3,'    closest match %s' % d_min)
                    newSE =  d_min.SE2
                    debugPrint(2,'  updating %s.%s   %s->%s' % (c.Name, SubElement, subElementName, newSE))
                    setattr(c, SubElement, newSE)
                    c.purgeTouched() #prevent constraint Proxy.execute being called when document recomputed.
                else:
                    debugPrint(3,'  leaving %s.%s as is, since subElement in old and new shape are equal' % (c.Name, SubElement))




