from core import *
from lib3D import fit_plane_to_surface1, fit_rotation_axis_to_surface1


class ConstraintSelectionObserver:
     def __init__(
             self,
             selectionGate,
             parseSelectionFunction, 
             taskDialog_title,
             taskDialog_iconPath,
             taskDialog_text,
             secondSelectionGate=None
     ):
          self.selections = []
          self.parseSelectionFunction = parseSelectionFunction
          self.secondSelectionGate = secondSelectionGate
          FreeCADGui.Selection.addObserver(self)  
          FreeCADGui.Selection.removeSelectionGate()
          FreeCADGui.Selection.addSelectionGate( selectionGate )
          wb_globals['selectionObserver'] = self
          self.taskDialog = SelectionTaskDialog(taskDialog_title, taskDialog_iconPath, taskDialog_text)
          FreeCADGui.Control.showDialog( self.taskDialog )
     def addSelection( self, docName, objName, sub, pnt ):
         debugPrint(4,'addSelection: docName,objName,sub = %s,%s,%s' % (docName, objName, sub))
         obj = FreeCAD.ActiveDocument.getObject(objName)
         debugPrint(1,'addSelection: docName,obj.Label,sub = %s,%s,%s' % (docName, obj.Label, sub)) # to print selection name
         self.selections.append( SelectionRecord( docName, objName, sub ))
         if len(self.selections) == 2:
             self.stopSelectionObservation()
             self.parseSelectionFunction( self.selections)
         elif self.secondSelectionGate is not None and len(self.selections) == 1:
             FreeCADGui.Selection.removeSelectionGate()
             FreeCADGui.Selection.addSelectionGate( self.secondSelectionGate )
     def stopSelectionObservation(self):
         FreeCADGui.Selection.removeObserver(self) 
         del wb_globals['selectionObserver']
         FreeCADGui.Selection.removeSelectionGate()
         FreeCADGui.Control.closeDialog()


class SelectionRecord:
    def __init__(self, docName, objName, sub):
        self.Document = FreeCAD.getDocument(docName)
        self.ObjectName = objName
        self.Object = self.Document.getObject(objName)
        self.SubElementNames = [sub]


class SelectionTaskDialog:
    def __init__(self, title, iconPath, textLines ):
        self.form = SelectionTaskDialogForm( textLines )
        self.form.setWindowTitle( title )    
        if iconPath != None:
            self.form.setWindowIcon( QtGui.QIcon( iconPath ) )
    def reject(self):
        wb_globals['selectionObserver'].stopSelectionObservation()
    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00400000 #cancel button
class SelectionTaskDialogForm(QtGui.QWidget):    
    def __init__(self, textLines ):
        super(SelectionTaskDialogForm, self).__init__()
        self.textLines = textLines 
        self.initUI()
    def initUI(self):
        vbox = QtGui.QVBoxLayout()
        for line in self.textLines.split('\n'):
            vbox.addWidget( QtGui.QLabel(line) )
        self.setLayout(vbox)


class SelectConstraintObjectsCommand:
    def Activated(self):
        constraintObj = FreeCADGui.Selection.getSelectionEx()[0].Object
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj1Name) )
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj2Name) )
    def GetResources(self): 
        return { 'MenuText': 'Select Objects' }
FreeCADGui.addCommand('assembly2_selectConstraintObjects', SelectConstraintObjectsCommand())

class SelectConstraintElementsCommand:
    def Activated(self):
        constraintObj = FreeCADGui.Selection.getSelectionEx()[0].Object
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj1Name), constraintObj.SubElement1 )
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj2Name), constraintObj.SubElement2 )
    def GetResources(self): 
        return { 'MenuText': 'Select Object Elements' }
FreeCADGui.addCommand('assembly2_selectConstraintElements', SelectConstraintElementsCommand())

def printSelection(selection):
    entries = []
    for s in selection:
        for e in s.SubElementNames:
            entries.append(' - %s:%s' % (s.ObjectName, e))
            if e.startswith('Face'):
                ind = int( e[4:]) -1 
                face = s.Object.Shape.Faces[ind]
                entries[-1] = entries[-1] + ' %s' % str(face.Surface)
    return '\n'.join( entries[:5] )
                
   
def getObjectFaceFromName( obj, faceName ):
    assert faceName.startswith('Face')
    ind = int( faceName[4:]) -1 
    return obj.Shape.Faces[ind]

class SelectionExObject:
    'allows for selection gate funtions to interface with classification functions below'
    def __init__(self, doc, Object, subElementName):
        self.doc = doc
        self.Object = Object
        self.ObjectName = Object.Name
        self.SubElementNames = [subElementName]
    

def planeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if str(face.Surface) == '<Plane object>':
                return True
            elif hasattr(face.Surface,'Radius'):
                return False
            elif str(face.Surface).startswith('<SurfaceOfRevolution'):
                return False
            else:
                plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'plane_norm %s, plane_pos %s, error_normalized %e' % (plane_norm, plane_pos, error_normalized))
                return error_normalized < 10**-6
    return False

def cylindricalPlaneSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if hasattr(face.Surface,'Radius'):
                return True
            elif str(face.Surface).startswith('<SurfaceOfRevolution'):
                return True
            elif str(face.Surface) == '<Plane object>':
                return False
            else:
                axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'fitted axis %s, center %s, error_normalized %e' % (axis, center,error_normalized))
                return error_normalized < 10**-6
    return False

def AxisOfPlaneSelected( selection ): #adding Planes/Faces selection for Axial constraints
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if str(face.Surface) == '<Plane object>':
                return True
            else:
                axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'fitted axis %s, center %s, error_normalized %e' % (axis, center,error_normalized))
                return error_normalized < 10**-6
    return False

def getObjectEdgeFromName( obj, name ):
    assert name.startswith('Edge')
    ind = int( name[4:]) -1 
    return obj.Shape.Edges[ind]

def CircularEdgeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Edge'):
            edge = getObjectEdgeFromName( selection.Object, subElement)
            if not hasattr(edge, 'Curve'): #issue 39
                return False
            if hasattr( edge.Curve, 'Radius' ):
                return True
            elif isLine(edge.Curve):
                return False
            else:
                try:
                    BSpline = edge.Curve.toBSpline()
                    arcs = BSpline.toBiArcs(10**-6)
                except:  #FreeCAD exception thrown ()
                    return False
                if all( hasattr(a,'Center') for a in arcs ):
                    centers = numpy.array([a.Center for a in arcs])
                    sigma = numpy.std( centers, axis=0 )
                    return max(sigma) < 10**-6
    return False


def isLine(param):
    if hasattr(Part,"LineSegment"):
        return isinstance(param,(Part.Line,Part.LineSegment))
    else:
        return isinstance(param,Part.Line)

def LinearEdgeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Edge'):
            edge = getObjectEdgeFromName( selection.Object, subElement)
            if not hasattr(edge, 'Curve'): #issue 39
                return False
            if isLine(edge.Curve):
                return True
            elif hasattr( edge.Curve, 'Radius' ):
                return False
            else:
                try:
                    BSpline = edge.Curve.toBSpline()
                    arcs = BSpline.toBiArcs(10**-6)
                except:  #FreeCAD exception thrown ()
                    return False
                if all(isLine(a) for a in arcs):
                    lines = arcs
                    D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                    return numpy.std( D, axis=0 ).max() < 10**-9
    return False

def vertexSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        return selection.SubElementNames[0].startswith('Vertex')
    return False

def getObjectVertexFromName( obj, name ):
    assert name.startswith('Vertex')
    ind = int( name[6:]) -1 
    return obj.Shape.Vertexes[ind]

def sphericalSurfaceSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            return str( face.Surface ).startswith('Sphere ')
    return False

def getSubElementPos(obj, subElementName):
    pos = None
    if subElementName.startswith('Face'):
        face = getObjectFaceFromName(obj, subElementName)
        surface = face.Surface
        if str(surface) == '<Plane object>':
            pos = getObjectFaceFromName(obj, subElementName).Faces[0].BoundBox.Center
            # axial constraint for Planes
            # pos = surface.Position
        elif all( hasattr(surface,a) for a in ['Axis','Center','Radius'] ):
            pos = surface.Center
        elif str(surface).startswith('<SurfaceOfRevolution'):
            pos = getObjectFaceFromName(obj, subElementName).Edges[0].Curve.Center
        else: #numerically approximating surface
            plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good plane fit
                pos = plane_pos
            axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good rotation_axis fix
                pos = center
    elif subElementName.startswith('Edge'):
        edge = getObjectEdgeFromName(obj, subElementName)
        if isLine(edge.Curve):
            pos = edge.Vertexes[-1].Point
        elif hasattr( edge.Curve, 'Center'): #circular curve
            pos = edge.Curve.Center
        else:
            BSpline = edge.Curve.toBSpline()
            arcs = BSpline.toBiArcs(10**-6)
            if all( hasattr(a,'Center') for a in arcs ):
                centers = numpy.array([a.Center for a in arcs])
                sigma = numpy.std( centers, axis=0 )
                if max(sigma) < 10**-6: #then circular curce
                    pos = centers[0]
            if all(isLine(a) for a in arcs):
                lines = arcs
                D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                if numpy.std( D, axis=0 ).max() < 10**-9: #then linear curve
                    return lines[0].value(0)
    elif subElementName.startswith('Vertex'):
        return  getObjectVertexFromName(obj, subElementName).Point
    if not pos is None:
        return numpy.array(pos)
    else:
        raise NotImplementedError("getSubElementPos Failed! Locals:\n%s" % formatDictionary(locals(),' '*4))

    
def getSubElementAxis(obj, subElementName):
    axis = None
    if subElementName.startswith('Face'):
        face = getObjectFaceFromName(obj, subElementName)
        surface = face.Surface
        if hasattr(surface,'Axis'):
            axis = surface.Axis
        elif str(surface).startswith('<SurfaceOfRevolution'):
            axis = face.Edges[0].Curve.Axis
        else: #numerically approximating surface
            plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good plane fit
                axis = plane_norm
            axis_fitted, center, error = fit_rotation_axis_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good rotation_axis fix
                axis = axis_fitted
    elif subElementName.startswith('Edge'):
        edge = getObjectEdgeFromName(obj, subElementName)
        if isLine(edge.Curve):
            axis = edge.Curve.tangent(0)[0]
        elif hasattr( edge.Curve, 'Axis'): #circular curve
            axis =  edge.Curve.Axis
        else:
            BSpline = edge.Curve.toBSpline()
            arcs = BSpline.toBiArcs(10**-6)
            if all( hasattr(a,'Center') for a in arcs ):
                centers = numpy.array([a.Center for a in arcs])
                sigma = numpy.std( centers, axis=0 )
                if max(sigma) < 10**-6: #then circular curce
                    axis = a.Axis
            if all(isLine(a) for a in arcs):
                lines = arcs
                D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                if numpy.std( D, axis=0 ).max() < 10**-9: #then linear curve
                    return D[0]
    if not axis is None:
        return numpy.array(axis)
    else:
        raise NotImplementedError("getSubElementAxis Failed! Locals:\n%s" % formatDictionary(locals(),' '*4))
