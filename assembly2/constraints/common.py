from assembly2.core import *
from assembly2.lib3D import *
from assembly2.selection import *
from .objectProxy import ConstraintObjectProxy
from .viewProviderProxy import ConstraintViewProviderProxy, repair_tree_view
from pivy import coin
from PySide import QtGui

__dir2__ = os.path.dirname(__file__)
GuiPath = os.path.expanduser ("~") #GuiPath = os.path.join( __dir2__, 'Gui' )


def recordConstraints( doc, s1, s2 ):
    constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
    with open(constraintFile, 'w') as outfile:
         outfile.write(make_string(s1.ObjectName)+'\n'+str(s1.Object.Placement.Base)+'\n'+str(s1.Object.Placement.Rotation)+'\n')
         outfile.write(make_string(s2.ObjectName)+'\n'+str(s2.Object.Placement.Base)+'\n'+str(s2.Object.Placement.Rotation)+'\n')
    constraints = [ obj for obj in FreeCAD.ActiveDocument.Objects if 'ConstraintInfo' in obj.Content ]
    #print constraints
    if len(constraints) > 0:
         constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
         if os.path.exists(constraintFile):
             with open(constraintFile, 'a') as outfile:
                 lastConstraintAdded = constraints[-1]
                 outfile.write(make_string(lastConstraintAdded.Name)+'\n')

def updateObjectProperties( c ):
    if hasattr(c,'FaceInd1'):
        debugPrint(3,'updating properties of %s' % c.Name )
        for i in [1,2]:
            c.addProperty('App::PropertyString','SubElement%i'%i,'ConstraintInfo')
            setattr(c,'SubElement%i'%i,'Face%i'%(getattr(c,'FaceInd%i'%i)+1))
            c.setEditorMode('SubElement%i'%i, 1) 
            c.removeProperty('FaceInd%i'%i)
        if hasattr(c,'planeOffset'):
            v = c.planeOffset
            c.removeProperty('planeOffset')
            c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
            c.offset = '%f mm' % v
        if hasattr(c,'degrees'):
            v = c.degrees
            c.removeProperty('degrees')
            c.addProperty("App::PropertyAngle","angle","ConstraintInfo")
            c.angle = v
    elif hasattr(c,'EdgeInd1'):
        debugPrint(3,'updating properties of %s' % c.Name )
        for i in [1,2]:
            c.addProperty('App::PropertyString','SubElement%i'%i,'ConstraintInfo')
            setattr(c,'SubElement%i'%i,'Edge%i'%(getattr(c,'EdgeInd%i'%i)+1))
            c.setEditorMode('SubElement%i'%i, 1) 
            c.removeProperty('EdgeInd%i'%i)
        v = c.offset
        c.removeProperty('offset')
        c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
        c.offset = '%f mm' % v
    if c.Type == 'axial' or c.Type == 'circularEdge':
        if not hasattr(c, 'lockRotation'):
            debugPrint(3,'updating properties of %s, to add lockRotation (default=false)' % c.Name )
            c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo")
    if FreeCAD.GuiUp:
        if not isinstance( c.ViewObject.Proxy , ConstraintViewProviderProxy):
            iconPaths = {
                'angle_between_planes':':/assembly2/icons/angleConstraint.svg',
                'axial':':/assembly2/icons/axialConstraint.svg',
                'circularEdge':':/assembly2/icons/circularEdgeConstraint.svg',
                'plane':':/assembly2/icons/planeConstraint.svg',
                'sphericalSurface': ':/assembly2/icons/sphericalSurfaceConstraint.svg'
            }
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, iconPaths[c.Type] )
