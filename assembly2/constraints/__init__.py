'''
assembly2 constraints are stored under App::FeaturePython object (constraintObj)

cName = findUnusedObjectName('axialConstraint')
c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = '...'
       
see http://www.freecadweb.org/wiki/index.php?title=Scripted_objects#Available_properties for more information
'''

import FreeCAD
import angleConstraint
import axialConstraint
import circularEdgeConstraint
import planeConstraint
import sphericalSurfaceConstraint
from viewProviderProxy import ConstraintViewProviderProxy
from assembly2.core import debugPrint


def updateOldStyleConstraintProperties( doc ):
    'used to update old constraint attributes, [object, faceInd] -> [object, subElement]...'
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            updateObjectProperties( obj )

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

def removeConstraint( constraint ):
    'required as constraint.Proxy.onDelete only called when deleted through GUI'
    doc = constraint.Document
    debugPrint(2, "removing constraint %s" % constraint.Name )
    if constraint.ViewObject != None: #do not this check is actually nessary ...
        constraint.ViewObject.Proxy.onDelete( constraint.ViewObject, None )
    doc.removeObject( constraint.Name )
