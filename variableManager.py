'''
In Freecad properties of surfaces and edges are expressed in absolute co-ordinates when acess object.shape .
Therefore when altering a objects placement variables as to get two surface aligned (or the like),
its recommended to the feature variables are converted into a relative co-ordinate system.
This relative co-ordinate system can then be transformed by object placements variables, when trying to determine the placement variables to solve the system.

6 variables per object
- x, y, z
first tried ZYX euler angles ( theta, phi, psi ) for rotational degrees of freedom, which did not work for all scenarios, now trying
- aximuth angle, elevation angle, rotation angle # where aximuth angle and elevation angle define the axis of rotation.


>>> d.part2.Placement.Base.x
1.999668037735
>>> d.part2.Shape.Faces[1].Surface.Position
Vector (1.999612710940575, 1.0000000000004354, 1.000000001530527)
>>> d.part2.Shape.Faces[1].Surface.Axis
Vector (-5.53267944549685e-05, 4.35523981361563e-13, -0.999999998469473)
>>> d.part2.Placement.Base.x = 6
>>> d.part2.Shape.Faces[1].Surface.Position
Vector (5.999944673204917, 1.0, 1.0000000015305273)
>>> d.part2.Shape.Faces[1].Surface.Axis
Vector (-5.532679508357674e-05, 0.0, -0.9999999984694729)
>>> d.part2.Placement.Rotation.Angle
1.5708516535900086
>>> d.part2.Placement.Rotation.Angle = 3.1
>>> d.part2.Shape.Faces[1].Surface.Position
Vector (5.000864849726721, 1.0, 1.9584193375667096)
>>> d.part2.Shape.Faces[1].Surface.Axis
Vector (-0.9991351502732795, 0.0, -0.04158066243329049)


'''


from lib3D import *
import numpy
from assembly2lib import debugPrint


class VariableManager:
    def __init__(self, doc, objectNames=None):
        self.doc = doc
        self.index = {}
        X = []
        if objectNames == None:
            objectNames = [obj.Name for obj in doc.Objects if hasattr(obj,'Placement')]
        for objectName in objectNames:
            self.index[objectName] = len(X)
            obj = doc.getObject(objectName)
            x, y, z = obj.Placement.Base.x, obj.Placement.Base.y, obj.Placement.Base.z
            axis, theta = quaternion_to_axis_and_angle( *obj.Placement.Rotation.Q )
            if theta <> 0:
                azi, ela = axis_to_azimuth_and_elevation_angles(*axis)
            else:
                azi, ela = 0, 0
            X = X + [ x, y, z, azi, ela, theta]
        self.X0 = numpy.array(X)
        self.X = self.X0.copy()

    def updateFreeCADValues(self, X, tol_base = 10.0**-8, tol_rotation = 10**-6):
        for objectName in self.index.keys():
            i = self.index[objectName]
            obj = self.doc.getObject(objectName)
            #obj.Placement.Base.x = X[i]
            #obj.Placement.Base.y = X[i+1]
            #obj.Placement.Base.z = X[i+2]
            if norm( numpy.array(obj.Placement.Base) - X[i:i+3] ) > tol_base: #for speed considerations only update placement variables if change in values occurs
                obj.Placement.Base = tuple( X[i:i+3] )
            azi, ela, theta =  X[i+3:i+6]
            axis = azimuth_and_elevation_angles_to_axis( azi, ela )
            new_Q = quaternion( theta, *axis ) #tuple type
            if norm( numpy.array(obj.Placement.Rotation.Q) - numpy.array(new_Q)) > tol_rotation:
                obj.Placement.Rotation.Q = new_Q

    def bounds(self):
        return [ [ -inf, inf], [ -inf, inf], [ -inf, inf], [-pi,pi], [-pi,pi], [-pi,pi] ] * len(self.index)

    def rotate(self, objectName, p, X):
        'rotate a vector p by objectNames placement variables defined in X'
        i = self.index[objectName]
        return azimuth_elevation_rotation( p, *X[i+3:i+6])

    def rotateUndo( self, objectName, p, X):
        i = self.index[objectName]
        R = azimuth_elevation_rotation_matrix(*X[i+3:i+6])
        return numpy.linalg.solve(R,p)

    def rotateAndMove( self, objectName, p, X):
        'rotate the vector p by objectNames placement rotation and then move using objectNames placement'
        i = self.index[objectName]
        return azimuth_elevation_rotation( p, *X[i+3:i+6]) + X[i:i+3]

    def rotateAndMoveUndo( self, objectName, p, X): # or un(rotate_and_then_move) #synomyn to get co-ordinates relative to objects placement variables.
        i = self.index[objectName]
        v = numpy.array(p) - X[i:i+3]
        R = azimuth_elevation_rotation_matrix(*X[i+3:i+6])
        return numpy.linalg.solve(R,v)


class ReversePlacementTransformWithBoundsNormalization:
    def __init__(self, obj):
        x, y, z = obj.Placement.Base.x, obj.Placement.Base.y, obj.Placement.Base.z
        self.offset = numpy.array([x, y, z]) #placement offset
        axis, theta = quaternion_to_axis_and_angle( *obj.Placement.Rotation.Q )
        if theta <> 0:
            azi, ela = axis_to_azimuth_and_elevation_angles(*axis)
        else:
            azi, ela = 0, 0
        self.R = azimuth_elevation_rotation_matrix( azi, ela, theta ) #placement rotation
        #now for bounds normalization
        #V = [ self.undoPlacement(v.Point) for v in obj.Shape.Vertexes] #no nessary in BoundBox is now used.
        V = [] 
        BB = obj.Shape.BoundBox
        extraPoints = []
        for z in [ BB.ZMin, BB.ZMax ]:
            for y in [ BB.YMin, BB.YMax ]:
                for x in [ BB.XMin, BB.XMax ] :
                    V.append( self.undoPlacement([x,y,z]) )
        V = numpy.array(V)
        self.Bmin = V.min(axis=0)
        self.Bmax = V.max(axis=0)
        self.dB = self.Bmax - self.Bmin

    def undoPlacement(self, p):
        # p = R*q + offset
        return numpy.linalg.solve( self.R, numpy.array(p) - self.offset )
    
    def unRotate(self, p):
        return numpy.linalg.solve( self.R, p)

    def __call__( self, p):
        q = self.undoPlacement(p)
        # q = self.Bmin + r* self.dB (where r is in normilezed coordinates)
        return (q - self.Bmin) / self.dB
    

