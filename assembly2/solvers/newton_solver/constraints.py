from assembly2.lib3D import *
from assembly2.selection import getSubElementPos, getSubElementAxis

class ConstraintPrototype:
    def __init__( self, doc, constraintObj, variableManager):
        '''
        assembly2 constraints are stored under App::FeaturePython object (constraintObj)

        cName = findUnusedObjectName('axialConstraint')
        c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
        c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = '...'
       
        see http://www.freecadweb.org/wiki/index.php?title=Scripted_objects#Available_properties for more information
        '''
        self.doc = doc
        self.constraintObj = constraintObj
        self.variableManager = variableManager
        self.registerVariables()

    def registerVariables( self ):
        raise RuntimeError, "ConstraintPrototype class not supposed to used directly"

    def errors( self ):
        'returns a list of errors, which the solver tries to reduce to 0'
        raise RuntimeError, "ConstraintPrototype class not supposed to used directly"
    
    def satisfied( self, eps=10**-3 ):
        return all( numpy.array(self.errors()) < eps )

    def objectNames( self):
        'for the general case...'
        return [self.constraintObj.Object1, self.constraintObj.Object2 ]

    def getPos(self, objName, subElement):
        obj =  self.doc.getObject( objName )
        return getSubElementPos(obj, subElement)

    def getAxis(self, objName, subElement):
        obj =  self.doc.getObject( objName )
        return getSubElementAxis(obj, subElement)



class AngleConstraint(ConstraintPrototype): 
     def registerVariables( self ):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 =  self.getAxis( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          a2 =  self.getAxis( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          self.a1_r = p1.rotate_undo( a1 ) #_r = relative to objects placement
          self.a2_r = p2.rotate_undo( a2 )
          self.degrees = self.constraintObj.angle.Value
          self.desired_dot_product = cos( self.degrees / 180 * pi )

     def errors(self):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 = p1.rotate( self.a1_r )
          a2 = p2.rotate( self.a2_r )          
          return [
               10**4 * ( self.desired_dot_product - numpy.dot(a1 , a2) )
               ]



class AxialConstraint(ConstraintPrototype): 
     def registerVariables( self ):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 =  self.getAxis( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          a2 =  self.getAxis( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          pos1 = self.getPos( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          pos2 = self.getPos( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          self.a1_r = p1.rotate_undo( a1 ) #_r = relative to objects placement
          self.a2_r = p2.rotate_undo( a2 )
          self.c1_r = p1.rotate_and_then_move_undo( pos1 )
          #debugPrint(4, 'surface1.center %s, rotate_and_then_move_undo %s' % (surface1.Center, self.c1_r))
          self.c2_r = p2.rotate_and_then_move_undo( pos2 )
          self.directionConstraint = self.constraintObj.directionConstraint

     def errors(self):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 = p1.rotate( self.a1_r )
          a2 = p2.rotate( self.a2_r )
          c1 = p1.rotate_and_then_move( self.c1_r )
          c2 = p2.rotate_and_then_move( self.c2_r )
          #debugPrint(4, 'a1 %s' % a1.__repr__())
          #debugPrint(4, 'a2 %s' % a2.__repr__())
          #debugPrint(4, 'c1 %s' % c1.__repr__())
          #debugPrint(4, 'c2 %s' % c2.__repr__())
          ax_prod = numpy.dot( a1, a2 )
          if self.directionConstraint == "none" :
               ax_const = (1 - abs(ax_prod))
          elif self.directionConstraint == "aligned":
               ax_const = (1 - ax_prod)
          else: #opposed
               ax_const = (1 + ax_prod)

          return [
               ax_const * 10**4, 
               distance_between_two_axes_3_points(c1,a1,c2,a2)
               ]

class CircularEdgeConstraint(ConstraintPrototype): 
     def registerVariables( self ):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 =  self.getAxis( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          a2 =  self.getAxis( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          pos1 = self.getPos( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          pos2 = self.getPos( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          self.a1_r = p1.rotate_undo( a1 ) #_r = relative to objects placement
          self.a2_r = p2.rotate_undo( a2 )
          self.c1_r = p1.rotate_and_then_move_undo( pos1 )
          #debugPrint(4, 'surface1.center %s, rotate_and_then_move_undo %s' % (surface1.Center, self.c1_r))
          self.c2_r = p2.rotate_and_then_move_undo( pos2 )
          self.directionConstraint = self.constraintObj.directionConstraint
          self.offset = self.constraintObj.offset.Value

     def errors(self):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 = p1.rotate( self.a1_r )
          a2 = p2.rotate( self.a2_r )
          c1 = p1.rotate_and_then_move( self.c1_r )
          c2 = p2.rotate_and_then_move( self.c2_r )
          #debugPrint(4, 'a1 %s' % a1.__repr__())
          #debugPrint(4, 'a2 %s' % a2.__repr__())
          #debugPrint(4, 'c1 %s' % c1.__repr__())
          #debugPrint(4, 'c2 %s' % c2.__repr__())
          ax_prod = numpy.dot( a1, a2 )
          if self.directionConstraint == "none" :
              ax_const = (1 - abs(ax_prod))
          elif self.directionConstraint == "aligned":
              ax_const = (1 - ax_prod)
          else: #opposed
              ax_const = (1 + ax_prod)

          dist = numpy.dot(a1, c1 - c2)

          return [
               ax_const * 10**4, 
               (dist - self.offset)**2,
               distance_between_two_axes_3_points(c1,a1,c2,a2)
               ]


class PlaneConstraint(ConstraintPrototype): 
     def registerVariables( self ):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 =  self.getAxis( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          a2 =  self.getAxis( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          pos1 = self.getPos( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          pos2 = self.getPos( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          self.a1_r = p1.rotate_undo( a1 ) #_r = relative to objects placement
          self.a2_r = p2.rotate_undo( a2 )
          self.pos1_r = p1.rotate_and_then_move_undo( pos1 )
          self.pos2_r = p2.rotate_and_then_move_undo( pos2 )
          self.planeOffset = self.constraintObj.offset.Value
          self.directionConstraint = self.constraintObj.directionConstraint


     def errors(self):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          a1 = p1.rotate( self.a1_r )
          a2 = p2.rotate( self.a2_r )
          pos1 = p1.rotate_and_then_move( self.pos1_r )
          pos2 = p2.rotate_and_then_move( self.pos2_r )
          dist = numpy.dot(a1, pos1 - pos2) #distance between planes
          #debugPrint(2, 'dist %f' % dist)
          ax_prod = numpy.dot( a1, a2 )
          if self.directionConstraint == "none" :
               ax_const = (1 - abs(ax_prod))
          elif self.directionConstraint == "aligned":
               ax_const = (1 - ax_prod)
          else: #opposed
               ax_const = (1 + ax_prod)
          
          return [
              ax_const * 10**5, 
              (dist - self.planeOffset)**2,
          ]


class SphericalSurfaceConstraint(ConstraintPrototype): 
     def registerVariables( self ):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          pos1 = self.getPos( self.constraintObj.Object1, self.constraintObj.SubElement1 )
          pos2 = self.getPos( self.constraintObj.Object2, self.constraintObj.SubElement2 )
          self.pos1_r = p1.rotate_and_then_move_undo( pos1 )
          self.pos2_r = p2.rotate_and_then_move_undo( pos2 )

     def errors(self):
          p1 = self.variableManager.getPlacementValues( self.constraintObj.Object1 )
          p2 = self.variableManager.getPlacementValues( self.constraintObj.Object2 )
          pos1 = p1.rotate_and_then_move( self.pos1_r )
          pos2 = p2.rotate_and_then_move( self.pos2_r )
          return [
              norm(pos1 - pos2)
          ]
