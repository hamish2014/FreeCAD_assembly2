'''
assembly2 constraints are stored under App::FeaturePython object (constraintObj)

cName = findUnusedObjectName('axialConstraint')
c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = '...'
       
see http://www.freecadweb.org/wiki/index.php?title=Scripted_objects#Available_properties for more information
'''

import FreeCAD
from assembly2.constraints import angleConstraint
from assembly2.constraints import axialConstraint
from assembly2.constraints import circularEdgeConstraint
from assembly2.constraints import planeConstraint
from assembly2.constraints import sphericalSurfaceConstraint
from assembly2.constraints.viewProviderProxy import ConstraintViewProviderProxy
from assembly2.core import debugPrint
from assembly2.constraints.common import updateObjectProperties

def updateOldStyleConstraintProperties( doc ):
    'used to update old constraint attributes, [object, faceInd] -> [object, subElement]...'
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            updateObjectProperties( obj )

def removeConstraint( constraint ):
    'required as constraint.Proxy.onDelete only called when deleted through GUI'
    doc = constraint.Document
    debugPrint(2, "removing constraint %s" % constraint.Name )
    if constraint.ViewObject != None: #do not this check is actually nessary ...
        constraint.ViewObject.Proxy.onDelete( constraint.ViewObject, None )
    doc.removeObject( constraint.Name )
