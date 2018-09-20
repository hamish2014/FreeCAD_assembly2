
from assembly2.lib3D import *
import numpy
from numpy import inf

class VariableManager:
    def __init__(self, doc):
        self.doc = doc
        self.placementVariables = {}
    def getPlacementValues(self, objectName):
        if not self.placementVariables.has_key(objectName):
            self.placementVariables[objectName] = PlacementVariables( self.doc, objectName )
        return self.placementVariables[objectName]
    def getValues(self):
        return sum([ pV.getValues() for key,pV in self.placementVariables.iteritems() if not pV.fixed ], [])
    def setValues(self, values):
        i = 0
        for key,pV in self.placementVariables.iteritems():
            if not pV.fixed:
                pV.setValues( values[ i*6: (i+1)*6 ] )
                i = i + 1
    def updateFreeCADValues(self):
        [ pV.updateFreeCADValues() for pV in self.placementVariables.values() if not pV.fixed ]
    def bounds(self):
        bounds = []
        for key,pV in self.placementVariables.iteritems():
            if not pV.fixed:
                bounds = bounds + pV.bounds()
        return bounds
    def peturbValues(self, objectsToPeturb):
        X = []
        for key,pV in self.placementVariables.iteritems():
            if not pV.fixed:
                y = numpy.array( pV.getValues() )
                if key in objectsToPeturb:
                    y[0:3] = y[0:3] + 42*( numpy.random.rand(3) - 0.5 )
                    y[3:6] = 2*pi *( numpy.random.rand(3) - 0.5 )
                X = X + y.tolist()
        return X
    def fixObj( self, objectName ):
        self.placementVariables[objectName].fixed = True
    def fixEveryObjectExcept(self, objectName):
        for key,pV in self.placementVariables.iteritems():
            if key <> objectName:
                pV.fixed = True
    def objFixed( self, objectName ):
        return self.placementVariables[objectName].fixed 

class PlacementVariables:
    def __init__(self, doc, objName):
        '''
        variables
        - x, y, z
        - theta, phi, psi  #using euler angles instead of quaternions because i think it will make the constraint problem easier to solver...

        NB - object,shapes,faces placement properties given in abosolute co-ordinates
        >>> App.ActiveDocument.Pocket.Placement
        Placement [Pos=(0,0,0), Yaw-Pitch-Roll=(0,0,0)]
        >>> Pocket.Shape.Faces[9].Surface.Center
        Vector (25.0, 15.0, 100.0)
        >>> Pocket.Placement.Base.x = 10
        >>> Pocket.Shape.Faces[9].Surface.Center
        Vector (35.0, 15.0, 100.0)
        >>> Pocket.Shape.Faces[9].Surface.Axis
        Vector (0.0, 0.0, 1.0)
        >>> Pocket.Placement.Rotation.Q = ( 1, 0, 0, 0) #rotate 180 about the x-axis
        >>> Pocket.Shape.Faces[9].Surface.Axis
        Vector (0.0, 0.0, -1.0)
        >>> Pocket.Shape.Faces[9].Surface.Center
        Vector (35.0, -15.0, -100.0)

        '''
        self.doc = doc
        self.objName = objName
        obj = doc.getObject(self.objName)
        self.x = obj.Placement.Base.x
        self.y = obj.Placement.Base.y
        self.z = obj.Placement.Base.z
        self.theta, self.phi, self.psi  = quaternion_to_euler( *obj.Placement.Rotation.Q )
        self.fixed = obj.fixedPosition

    def getValues(self):
        assert not self.fixed
        return [self.x, self.y, self.z, self.theta, self.phi, self.psi]

    def bounds(self):
        return [ [ -inf, inf], [ -inf, inf], [ -inf, inf], [-pi,pi], [-pi,pi], [-pi,pi] ]

    def setValues(self, values):
        assert not self.fixed
        self.x, self.y, self.z, self.theta, self.phi, self.psi = values

    def updateFreeCADValues(self):
        '''http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions '''        
        assert not self.fixed
        obj = self.doc.getObject( self.objName )
        obj.Placement.Base = ( self.x, self.y, self.z )
        obj.Placement.Rotation.Q = euler_to_quaternion( self.theta, self.phi, self.psi )
        #self.doc.getObject(self.objName).touch()
    
    def rotate( self, p):
        #debugPrint( 3, "p %s" % p)
        #debugPrint( 3, "theta %2.1f, phi %2.1f, psi %2.1f" % ( self.theta/pi*180, self.phi/pi*180, self.psi/pi*180 ))
        #debugPrint( 3, 'result %s' % euler_ZYX_rotation( p, self.theta, self.phi, self.psi ))
        return euler_ZYX_rotation( p, self.theta, self.phi, self.psi )

    def rotate_undo( self, p ): # or unrotate
        R = euler_ZYX_rotation_matrix( self.theta, self.phi, self.psi )
        return numpy.linalg.solve(R,p)

    def rotate_and_then_move( self, p):
        return self.rotate(p) + numpy.array([ self.x, self.y, self.z ])

    def rotate_and_then_move_undo( self, p): # or un(rotate_and_then_move)
        return self.rotate_undo( numpy.array(p) - numpy.array([ self.x, self.y, self.z ]) )        
    
