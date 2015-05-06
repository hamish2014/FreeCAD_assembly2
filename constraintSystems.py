'''
Solver approach
---------------

Adjust the placement variables (position and rotation variables, 6 for each object) as satify all constraints;
by adding one constraint at a time and adjusting the degrees-of-freedom.
Ideally, this degrees-of-freedom can be identified, so that they can be adjusted with having to check previous constraints.
For non-simple systems this is not practical however as there are to many combinations to hard-code.

Therefore a heiracical constraint system is used.
When attempting the solve the current constraint, the placement variables are also adjusted/refreshed according to the previous constaints to allow for non-perfect degress-of-freedom.
This is done in a heirachical way, with parent constraints mimimally adjust the placement variables as to satify there constraints.

Nomeclature

X - placement variables
D - degrees of freedom, where D is a subset of X,  which can idealy be altered without violating the constraints already added to the system.
Y - degrees of freedom values

see Assembly2/docs folder for more.

'''

from assembly2lib import *
from lib3D import *
import numpy
from numpy import pi, inf
from numpy.linalg import norm
from solverLib import *
from degreesOfFreedom import *

class Assembly2SolverError(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return self.parameter

#debugPrint, replaced to reduce overhead
def dp( msg ):
    FreeCAD.Console.PrintMessage(msg + '\n')
# debugPrint(2, msg)   ----> if debugPrint.level >= 2: dp(msg) 

class ConstraintSystemPrototype:
    label = '' #over-ride in inheritence
    solveConstraintEq_tol = 10**-9
    def __init__(self, parentSystem, variableManager, constraintObj, constraintValue ):
        self.parentSystem = parentSystem
        self.variableManager = variableManager
        # not doing self.X = self.variableManager.X, as even though linked via numpy array, problems can occur i do something later like self.X  = X_org, which breaks the link.
        self.constraintObj = constraintObj
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        self.obj1Name = obj1Name
        self.obj2Name = obj2Name
        self.subElement1 = constraintObj.SubElement1
        self.subElement2 = constraintObj.SubElement2
        self.constraintValue = constraintValue
        self.childSystem = None
        parentSystem.childSystem = self
        doc = variableManager.doc
        assert parentSystem.containtsObject( obj1Name ) or parentSystem.containtsObject( obj2Name )
        sys2ObjName = None
        if not parentSystem.containtsObject( obj1Name ):
            sys2ObjName = obj1Name
        if not parentSystem.containtsObject( obj2Name ):
            sys2ObjName = obj2Name
        if sys2ObjName <> None:
            if getattr( doc.getObject( sys2ObjName  ), 'fixedPosition', False ):
                self.sys2 = FixedObjectSystem( variableManager, sys2ObjName )
            else:
                self.sys2 = FreeObjectSystem( variableManager, sys2ObjName )
        else:
            self.sys2 = EmptySystem()
        if debugPrint.level >= 4: dp('%s - sys2 %s' % (self.label, self.sys2.str() ) )
        self.init2()
        self.solveConstraintEq()      
        if debugPrint.level >= 3 : dp('  resulting system:\n%s' % self.str(indent=' '*4, addDOFs=debugPrint.level>3))
        
    def init2(self):
        pass

    def containtsObject( self, objName ):
        if self.obj1Name == objName:
            return True
        elif self.obj2Name == objName:
            return True
        return self.parentSystem.containtsObject( objName )

    def solveConstraintEq( self ):
        tol = self.solveConstraintEq_tol
        PLO = 0 if not self.childSystem else 1 #print level offset
        if abs( self.constraintEq_value( self.variableManager.X) ) > tol: #constraint violated
            self.solveConstraintEq_dofs = [ d for d in self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom ]#if not d.assignedValue ]
            if len(self.solveConstraintEq_dofs) == 0: 
                raise Assembly2SolverError,"%s no degrees-of-freedom to adjust to satify constraints:\n%s" % (self.str(), self.strSystemTree())
            else:
                if self.analyticalSolution(): #if analytical solution then will update X
                #if False:
                    #self.analyticalSolution() #forcing analytical solution to run twice as to decrease numerical error
                    if abs( self.constraintEq_value(self.variableManager.X) ) > tol:
                        if debugPrint.level >= 4+PLO: dp('  **numerical round off error in analytical solution repeating')
                        self.analyticalSolution()
                else: #numerical solution
                    Y0 =      [ d.getValue() for d in self.solveConstraintEq_dofs ]
                    if debugPrint.level >= 4+PLO: dp('%s: attempting to find solution numerically' % (self.str()))
                    yOpt = solve_via_Newtons_method( 
                        self.constraintEq_f, 
                        Y0, #Y0, 
                        [ d.maxStep() for d in self.solveConstraintEq_dofs ], #maxStep, while not really, more like recommended max step...
                        f_tol=tol, 
                        x_tol=0, 
                        maxIt=42, 
                        randomPertubationCount=2, 
                        lineSearchIt=10,
                        debugPrintLevel=debugPrint.level-2-PLO, 
                        printF= lambda txt: debugPrint(2, txt ),
                        record = not self.childSystem #only record top level optimization.
                        )
                    self.constraintEq_setY(yOpt) #this will automatically update X
            if abs( self.constraintEq_value(self.variableManager.X) ) > tol:
                raise Assembly2SolverError,"%s abs( self.constraintEq_value(self.X) ) > tol [%e > %e]. Constraint Tree:\n%s" % (self.str(), abs( self.constraintEq_value(self.variableManager.X) ), tol, self.strSystemTree())
        else:
            pass
            #debugPrint(4+PLO, '    solveConstraintEq for %s already satisfied, neither numerical or analytical solution required' % self.str())
        if not hasattr( self, 'degreesOfFreedom' ):
            self.dof_updated_analytically = self.generateDegreesOfFreedomAnalytically( ) #Analytical, as in preprogrammed  solution available.
            if not self.dof_updated_analytically:
                self.generateDegreesOfFreedomNumerically( )
        else:
            if self.dof_updated_analytically:
                self.updateDegreesOfFreedomAnalytically( )
            else:
                self.updateDegreesOfFreedomNumerically( )

    def constraintEq_setY(self, Y):
        for d,y in zip( self.solveConstraintEq_dofs, Y):
            d.setValue(y)
        self.parentSystem.update()
        self.sys2.update()

    def update(self):
        if self.parentSystem <> None:
            self.parentSystem.update()
        self.solveConstraintEq()  

    def constraintEq_f( self, Y ):
        #print(self.variableManager.X)
        self.constraintEq_setY(Y)
        f_X = self.constraintEq_value(self.variableManager.X)
        PLO = 0 if not self.childSystem else 1 #print level offset
        if debugPrint.level >= 6+PLO: dp('constraintEq_f, X %s, f(X) %s' % (self.variableManager.X,f_X))
        return f_X
    def constraintEq_value( self, X ):
        raise Assembly2SolverError, 'ConstraintSystemPrototype not supposed to be called directly'

    def analyticalSolution(self):
        return False

    def generateDegreesOfFreedomAnalytically( self ):
        raise Assembly2SolverError, 'ConstraintSystemPrototype not supposed to be called directly'

    def updateDegreesOfFreedomAnalytically( self ):
        raise Assembly2SolverError, 'ConstraintSystemPrototype not supposed to be called directly'                    

    def getPos(self, objName, subElement):
        obj =  self.variableManager.doc.getObject( objName )
        pos = None
        if subElement.startswith('Face'):
            surface = getObjectFaceFromName(obj, subElement).Surface
            if str(surface) == '<Plane object>':
                pos = surface.Position
            elif all( hasattr(surface,a) for a in ['Axis','Center','Radius'] ):
                pos = surface.Center
            else:
                raise NotImplementedError,"getPos %s" % str(surface)
        elif subElement.startswith('Edge'):
            edge = getObjectEdgeFromName(obj, subElement)
            if isinstance(edge.Curve, Part.Line):
                pos = edge.Curve.StartPoint
            else: #circular curve
                pos = edge.Curve.Center    
        elif subElement.startswith('Vertex'):
            return  getObjectVertexFromName(obj, subElement).Point
        if pos <> None:
            return numpy.array(pos)
        else:
            raise NotImplementedError,"subElement %s" % subElement
        #elif self.featureType == 'circle':
        #     return obj.Shape.Edges[featureInd].Curve.Center

    def getAxis(self, objName, subElement):
        obj =  self.variableManager.doc.getObject( objName )
        axis = None
        if subElement.startswith('Face'):
            axis = getObjectFaceFromName(obj, subElement).Surface.Axis
        elif subElement.startswith('Edge'):
            edge = getObjectEdgeFromName(obj, subElement)
            if isinstance(edge.Curve, Part.Line):
                axis = edge.Curve.tangent(0)[0]
            else: #circular curve
                axis =  edge.Curve.Axis
        if axis <> None:
            return numpy.array(axis)
        else:
            raise NotImplementedError,"subElement %s" % subElement

    def str(self, indent='', addDOFs=False):
        txt = '%s<%s System %s:%s-%s:%s heirachy %i>' % (indent, self.label, self.obj1Name, self.subElement1, self.obj2Name, self.subElement2, self.numberOfParentSystems())
        if addDOFs and hasattr( self, 'degreesOfFreedom'):
            txt = txt + ' %i degrees of freedom:' % len(self.degreesOfFreedom)
            txt = txt + ''.join( [ '\n%s%s' %(indent, d.str('  ')) for d in  self.degreesOfFreedom ] )
        return txt

    def numberOfParentSystems(self):
        count = 0
        sys = self
        while sys.parentSystem <> None:
            sys = sys.parentSystem
            count = count + 1
        return count

    def strSystemTree(self, dofs=True):
        txt = self.str(addDOFs=dofs)
        sys = self
        indent = ''
        while sys.parentSystem <> None:
            indent = indent+' '*4 if dofs else indent+' '*2
            if not isinstance(sys.sys2, EmptySystem):
                txt = txt + '\n' + sys.sys2.str(indent, addDOFs=dofs)
            txt = txt + '\n' + sys.parentSystem.str(indent, addDOFs=dofs)
            sys = sys.parentSystem
        return txt

    def generateDegreesOfFreedomNumerically(self ):
        if debugPrint.level >= 4: dp('  attempting to generate new degrees-of-freedom numerically')
        D = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.solveConstraintEq_dofs = D #if not d.assignedValue check unnessary as generateDegreesOfFreedomNumerically is only called on top level
        if len(D) == 0:
            self.generateDegreesOfFreedomNumerically_case = 0 #system has no degrees of freedom, so nothing to do
            self.degreesOfFreedom = D    
            return
        else:
            X_org = self.variableManager.X.copy()
            yOpt = [ d.getValue() for d in self.solveConstraintEq_dofs ] #values update in solve equation.
            df_dy = GradientApproximatorForwardDifference(self.constraintEq_f)(numpy.array(yOpt))
            #debugPrint(5, '  df_dy == %s' % str(df_dy))
            self.variableManager.X = X_org
            if all(df_dy == 0):
                if debugPrint.level >= 4: dp('  generateDegreesOfFreedomNumerically, all(df_dy == 0), so assuming constraint is reduntant.')
                self.generateDegreesOfFreedomNumerically_case = 0
                self.degreesOfFreedom = D
                return
            else:
                removeInd = None
                if len(df_dy) - sum(df_dy == 0) == 1:
                    if debugPrint.level >= 4: dp('  generateDegreesOfFreedomNumerically, len(df_dy) - sum(df_dy == 0) == 1, removing dof with gradient <> 0')
                    removeInd = list(df_dy == 0).index(False)
                elif len(df_dy) - sum(abs(df_dy) < max(abs(df_dy))*1e-6) == 1:
                    if debugPrint.level >= 4: dp('  generateDegreesOfFreedomNumerically, len(df_dy) - sum(abs(df_dy) < max(abs(df_dy))*1e-6) == 1, removing dof with largest gradient')
                    removeInd = list( abs(df_dy) == max(abs(df_dy)) ).index(True)
                self.generateDegreesOfFreedomNumerically_case = 0
                if debugPrint.level >= 4: dp('    removing %s' % D[removeInd])
                self.degreesOfFreedom = [ d for i,d in enumerate(D) if i <> removeInd ]
                return
               
                
        raise NotImplementedError,'generateDegreesOfFreedomNumerically Logic not programmed for the reduction of degrees of freedom with df_dy=%s, self.solveConstraintEq_dofs:\n%s' % (df_dy,'\n'.join(d.str('  ') for d in self.solveConstraintEq_dofs ))

    def updateDegreesOfFreedomNumerically( self ):
        if self.generateDegreesOfFreedomNumerically_case == 0:
            return 
        raise NotImplementedError
    


class FixedObjectSystem(ConstraintSystemPrototype):
    def __init__(self, variableManager, objName):
        self.variableManager = variableManager
        self.objName = objName
        self.degreesOfFreedom = []
        self.parentSystem = None
    def containtsObject(self, objName):
        return self.objName == objName
    def solveConstraintEq( self ):
        pass
    def update(self):
        pass
    def str(self, indent='', addDOFs=False):
        return '%s<FixedObjectSystem %s> %s' % (indent, self.objName, '0 degrees of freedom' if addDOFs else '')

class EmptySystem( FixedObjectSystem ):
    def __init__(self ):
        self.degreesOfFreedom = []
    def containtsObject(self, objName):
        return False
    def str(self, indent=''):
        return '%s<EmptySystem>' % (indent)   

class FreeObjectSystem( FixedObjectSystem ):
    def __init__(self, variableManager, objName):
        self.variableManager = variableManager
        self.objName = objName
        self.degreesOfFreedom = [ PlacementDegreeOfFreedom( self, objName, j ) for j in range(6) ]
    def str(self, indent='', addDOFs=False):
        txt = '%s<FreeObjectSystem %s>' % (indent, self.objName)
        if addDOFs:
            txt = txt + ' %i degrees of freedom:' % len(self.degreesOfFreedom)
            txt = txt + ''.join( [ '\n%s%s' %(indent, d.str('  ')) for d in  self.degreesOfFreedom ] )
        return txt


class AxisAlignmentUnion(ConstraintSystemPrototype):
    label = 'AxisAlignmentUnion'
    solveConstraintEq_tol = 10**-9

    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.a1_r = vM.rotateUndo( self.obj1Name, self.getAxis(self.obj1Name, self.subElement1), vM.X0 )
        self.a2_r = vM.rotateUndo( self.obj2Name, self.getAxis(self.obj2Name, self.subElement2), vM.X0 )
        #if debugPrint.level >= 4: dp('    a1_r %s, a2_r %s, directionConstraintFlag %s' % (self.a1_r, self.a2_r, self.constraintValue))

    def constraintEq_value( self, X ):
        vM = self.variableManager
        a = vM.rotate( self.obj1Name, self.a1_r, X )
        b = vM.rotate( self.obj2Name, self.a2_r, X )
        ax_prod = dotProduct( a,b )
        directionConstraintFlag = self.constraintValue
        if directionConstraintFlag == "none" : 
            return (1 - abs(ax_prod))
        elif directionConstraintFlag == "aligned":
            return (1 - ax_prod)
        else:
            return (1 + ax_prod)

    def analyticalSolution(self):
        D = self.solveConstraintEq_dofs #degrees of freedom
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in D if d.objName == objName and d.rotational() ]
            if len(matches) == 3:
                if debugPrint.level >= 3: dp('%s analyticalSolution available: %s has free rotation.'% (self.label, objName))
                vM = self.variableManager
                if objName == self.obj1Name: #then object1 has has free rotation
                    v = self.a1_r
                    v_ref = vM.rotate( self.obj2Name, self.a2_r, vM.X )
                else:
                    v = self.a2_r
                    v_ref = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                if debugPrint.level >= 4: dp('    v %s, v_ref %s, directionConstraintFlag %s' % (v, v_ref, self.constraintValue))
                axis, angle = rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( v, v_ref )
                angle = self.analyticalSolutionAdjustAngle( angle, axis, v, v_ref )
                if debugPrint.level >= 4: dp('    analyticalSolution:  axis %s, angle %s.'% (axis, angle))
                #v_rotated = dotProduct( axis_rotation_matrix( angle, *axis), v)
                #if debugPrint.level >= 4: dp('    v_rotated %s' % v_rotated )
                azi, ela = axis_to_azimuth_and_elevation_angles(*axis)
                assert matches[0].ind % 6 == 3 and matches[1].ind % 6 == 4 and matches[2].ind % 6 == 5
                matches[0].setValue(azi)
                matches[1].setValue(ela)
                matches[2].setValue(angle)
                self.parentSystem.update() # required other constraints may effect by parts rotation ....
                self.sys2.update()
                return True
            elif len(matches) == 1 and isinstance( matches[0], AxisRotationDegreeOfFreedom ):
                d = matches[0]
                vM = self.variableManager
                d.setValue(0) #make life easier!
                if d.objName == self.obj1Name:
                    v = vM.rotate( self.obj1Name, self.a1_r, vM.X ) 
                    v_ref = vM.rotate( self.obj2Name, self.a2_r, vM.X )
                else:
                    v = vM.rotate( self.obj2Name, self.a2_r, vM.X )
                    v_ref = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                axis_component_v_ref = dot(d.axis, v_ref)
                axis_component_v     = dot(d.axis, v_ref)
                # may still work axis alignment if axis_component_v_ref <> 0, axis_component_v <> 0
                # problem for angleUnions in this case, therefore checking at end if analytical solution will work at end.
                v_angle = d.vectorsAngleInDofsCoordinateSystem( v ) #determining v_angle, v's angle will not be zero!!! THIS CAUSED ME GREY HAIR lol:)
                v_ref_angle = d.vectorsAngleInDofsCoordinateSystem( v_ref ) 
                if debugPrint.level >= 4: dp('  %s-%s analyticalSolution possibly available, v_angle %f, v_ref_angle %f'% (self.label, objName, v_angle, v_ref_angle))
                if self.label == 'AxisAlignmentUnion':
                    directionConstraintFlag = self.constraintValue
                    if directionConstraintFlag == "aligned":
                        d.setValue( v_ref_angle - v_angle)
                    elif directionConstraintFlag =="opposed":
                        d.setValue( v_ref_angle - pi - v_angle)
                    elif directionConstraintFlag == "none":
                        if dotProduct(v,v_ref) < 0 :
                            d.setValue( v_ref_angle - pi - v_angle)
                        else:
                            d.setValue( v_ref_angle - v_angle )
                elif self.label == 'AngleUnion':
                    #we want v_angle - v_ref_angle = self.constraintValue
                    actualDiff =  v_angle - v_ref_angle
                    diff = actualDiff - self.constraintValue
                    #if debugPrint.level >= 4: dp('    angle diff %f' % diff)
                    d.setValue( v_ref_angle - v_angle - self.constraintValue )
                else: 
                    raise NotImplementedError
                #print(d)
                self.parentSystem.update()
                self.sys2.update()
                #print(d)
                #checking if solution worked
                #if debugPrint.level >= 4: dp('    v_angle  %f  v_ref_angle  %f  self.constraintValue %s' % (d.vectorsAngleInDofsCoordinateSystem( v),d.vectorsAngleInDofsCoordinateSystem( v_ref ),self.constraintValue))
                error = abs(self.constraintEq_value(vM.X))
                if error < 10**-9:
                    if debugPrint.level >= 4: dp('    %s-%s  analyticalSolution solution worked, error %e'% (self.label, objName, error))
                    return True
                else:
                    if debugPrint.level >= 4: dp('    %s-%s  analyticalSolution solution failed, error %e'% (self.label, objName, error))
                #d = matches[0]
                ##q_0, q_1, q_2, q_3 =  d.Q1 
                #vM = self.variableManager
                #if objName == self.obj1Name: #then object1 has rotation about d.axis
                #    #v = quaternion_rotation( self.a1_r, q_1, q_2, q_3, q_0 )
                #    v = dotProduct( d.R_to_align_axis, self.a1_r) #where self.R_to_align_axis refers to constraint system which paraments the AxisRotationDegreeOfFreedom
                #    v_ref = vM.rotate( self.obj2Name, self.a2_r, vM.X )
                #else:
                #    #v = quaternion_rotation( self.a2_r, q_1, q_2, q_3, q_0 )
                #    v = dotProduct( d.R_to_align_axis, self.a2_r)
                #    v_ref = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                #axis, angle = rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( v, v_ref)
                #alignmentError = 1 - abs(dotProduct(axis, d.axis))
                #if abs(angle) < 10**-6 or abs(angle -pi) < 10**-6: #then v == v_ref, then random perpendicular axis returned 2 lines up
                #    if debugPrint.level >= 4: dp('  %s-%s analyticalSolution correcting error on account of v and v_ref being on same axis'% (self.label, objName))
                #    axis = d.axis
                #    alignmentError = 0
                #if debugPrint.level >= 4: dp('  %s-%s analyticalSolution alignment error %e, angle %f'% (self.label, objName, alignmentError, angle))
                #if alignmentError < self.solveConstraintEq_tol:
                #    if debugPrint.level >= 3: dp('  %s analyticalSolution available: %s has free rotation about the required axis.'% (self.label, objName))
                #    #if dotProduct(axis, d.axis) < 0: #no longer required since d.axis added to rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector()
                #    #    axis = -axis
                #    #    angle = -angle
                #    angle = self.analyticalSolutionAdjustAngle( angle, axis, v, v_ref )
                #    if debugPrint.level >= 4: dp('    analyticalSolution:  axis %s, angle %s.'% (axis, angle))
                #    if debugPrint.level >= 4: dp('d %s' % d)
                #    d.setValue(d.getValue() + angle)
                #    self.parentSystem.update()
                #    self.sys2.update()
                #    return True
        return False

    def analyticalSolutionAdjustAngle( self, angle, axis, v, v_ref ):
        #checking angle against directionConstraintFlag
        v_rotated = dotProduct( axis_rotation_matrix( angle, *axis), v)
        ax_prod = dotProduct( v_rotated, v_ref )
        #print('ax_product %1.2f' % ax_prod)
        directionConstraintFlag = self.constraintValue
        if directionConstraintFlag == "aligned" and ax_prod < 0: #instead of ax_prod == -1 (mitigate precision errors)
            angle = angle - pi
        elif directionConstraintFlag =="opposed" and ax_prod > 0:
            angle = angle - pi
        elif directionConstraintFlag == "none"  and angle > pi/2:
            angle = angle - pi
        return angle

    def generateDegreesOfFreedomAnalytically( self ):
        dofs = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        success = False
        #first try to look for an object which has 3 rotational degrees of freedom'
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in dofs if d.objName == objName and d.rotational() ]
            if len(matches) == 3:
                if debugPrint.level >= 4: dp('%s Logic "%s": reducing from 3 to 1 rotational degree of freedom (2 rotation degrees fixed in defining axis of rotation)' % (self.label, objName))
                self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                self.degreesOfFreedom.append( AxisRotationDegreeOfFreedom( self, objName) )
                self.degreesOfFreedom_updateInd = len(self.degreesOfFreedom) -1
                success = True
                break
            elif len(matches) == 1 and isinstance(matches[0], AxisRotationDegreeOfFreedom):
                vM = self.variableManager
                a = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                if 1 - abs(dotProduct(a, matches[0].axis)) < self.solveConstraintEq_tol: #
                    if debugPrint.level >= 4: dp('%s Logic "%s": AxisRotationDegreeOfFreedom with same axis already exists not reducing dofs for part' % (self.label, objName))
                    self.degreesOfFreedom_updateInd = -1
                    self.degreesOfFreedom = dofs
                    success = True
                else:
                    if debugPrint.level >= 4: dp('%s Logic "%s": 2 different rotation axis specified, therefore fixing rotation (0 rotational degrees of freedom)' % (self.label, objName))
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.degreesOfFreedom_updateInd = -1
                    success = True
                    break
            elif len(matches) == 0:
                if debugPrint.level >= 4: dp('%s Logic "%s": no rotational degrees of freedom ignoring.' % (self.label, objName))
                #    self.degreesOfFreedom = dofs
                #    self.degreesOfFreedom_updateInd = -1
                #    success = True
        if len(matches) > 0 and self.constraintValue == "none": #then assign direction, to make users and solvers life easier, #outside loop due to break
            #len(matches) > 0 required as assigning a direction flag to a rotationally fixed object, will lock a previous direction flag
            vM = self.variableManager
            a = vM.rotate( self.obj1Name, self.a1_r, vM.X )
            b = vM.rotate( self.obj2Name, self.a2_r, vM.X )
            self.constraintValue = "aligned"  if dotProduct( a,b ) > 0 else "opposed"
            self.constraintObj.directionConstraint = ["aligned","opposed"]
            self.constraintObj.directionConstraint = self.constraintValue    
        if success:
            self.updateDegreesOfFreedomAnalytically()
        #else:
        #    if debugPrint.level >= 3: dp('%s.generateDegreesOfFreedomAnalytical Logic not programmed for the reduction of degrees of freedom of:\n%s' % (self.label,'\n'.join(d.str('  ') for d in dofs ))
        return success
        
    def updateDegreesOfFreedomAnalytically( self ):
        if self.degreesOfFreedom_updateInd > -1:
            vM = self.variableManager
            d = self.degreesOfFreedom[ self.degreesOfFreedom_updateInd ]
            if d.objName == self.obj1Name:
                a = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                d.setAxis( a, self.a1_r )
            else:
                a = vM.rotate( self.obj2Name, self.a2_r, vM.X )
                d.setAxis( a, self.a2_r )

class AngleUnion(AxisAlignmentUnion):
    label = 'AngleUnion'
    def constraintEq_value( self, X ):
        vM = self.variableManager
        a = vM.rotate( self.obj1Name, self.a1_r, X )
        b = vM.rotate( self.obj2Name, self.a2_r, X )
        return cos(self.constraintValue) - dotProduct( a,b )
        # for another day
        #c = crossProduct( a, b)
        #if norm(c) > 0:
        #    axis = normalize(c)
        #    axis3 = normalize ( crossProduct(a, c) )
        #    adj = dotProduct( b, a ) #adjacent
        #    opp = dotProduct( b, axis3 ) #oppersite
        #    angle = numpy.arctan2( opp, adj )
        #else: #either 0 or 180 degrees
        #    angle = 0 if dotProduct( a,b ) == 1 else pi
        #return self.constraintValue - angle

    def analyticalSolutionAdjustAngle( self, actual_angle, axis, v, v_ref ):
        desired_angle = self.constraintValue
        correction = actual_angle - desired_angle
        return correction
            

class PlaneOffsetUnion(ConstraintSystemPrototype):
    label = 'PlaneOffsetUnion'
    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.a1_r =   vM.rotateUndo( self.obj1Name, self.getAxis(self.obj1Name, self.subElement1), vM.X0 )
        self.pos1_r = vM.rotateAndMoveUndo( self.obj1Name, self.getPos(self.obj1Name, self.subElement1), vM.X0 )
        self.pos2_r = vM.rotateAndMoveUndo( self.obj2Name, self.getPos(self.obj2Name, self.subElement2), vM.X0 )
        
    def constraintEq_value( self, X ):
        vM = self.variableManager
        a = vM.rotate( self.obj1Name, self.a1_r, X )
        pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, X )
        pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, X )
        dist = dotProduct(a, pos1 - pos2) #distance between planes
        return dist - self.constraintValue

    def analyticalSolution(self):
        D = self.solveConstraintEq_dofs #degrees of freedom
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in D if d.objName == objName and not d.rotational() ]
            if len(matches) > 0:
                #if debugPrint.level >= 4: dp('    %s %s has linear displacement degrees of freedom, checking for analyticalSolution.'% (self.label, objName))
                vM = self.variableManager
                a = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                for j in reversed(range(len(matches))):
                    if abs( dot(a, matches[j].directionVector) ) < 10**-9:
                        del matches[j]
                if len(matches) == 0 :
                    if debugPrint.level >= 4: dp('    %s %s aborting analytical solution, since dof perpindicular to required displacement.'% (self.label, objName))
                    continue 
                if debugPrint.level >= 3: dp('    %s analyticalSolution available by moving %s.'% (self.label, objName))
                pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, vM.X )
                pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, vM.X )
                error =  dotProduct(a, pos1 - pos2) - self.constraintValue
                if objName == self.obj1Name:
                    error = -error
                #print('error * a : %s' % (error*a))
                A = numpy.array( [[ dot(a,m.directionVector) for m in matches]] )
                V = numpy.linalg.lstsq(A,[error])[0]
                for m,v in zip(matches, V):
                    m.setValue( m.getValue() + v )
                self.parentSystem.update() 
                self.sys2.update()
                return True
        return False

    def generateDegreesOfFreedomAnalytically( self ):
        dofs = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        #first try to look for an object which has 3 linear motion degrees of freedom'
        success = False
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in dofs if d.objName == objName and not d.rotational() ]
            if len(matches) == 3:
                if debugPrint.level >= 4: dp('PlaneOffsetUnion Logic: %s - reducing linear displacement degrees of freedom from 3 to 2' % objName)
                self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName) )
                self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName) )
                self.dofs_removed = matches
                success = True
                break
            elif len(matches) == 2:
                vM = self.variableManager
                planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                c = crossProduct( matches[0].directionVector, matches[1].directionVector)
                planeNormalMatches = c/norm(c)
                if norm(planeNormalVector - planeNormalMatches) < 10 **-6: #then constraint redudant
                    if debugPrint.level >= 4: dp('PlaneOffsetUnion Logic: %s - plane constraint with normal already exist, not reducing dofs for part' % objName)
                    #self.degreesOfFreedom =  dofs
                    #self.dofs_removed = []
                    #success = True
                else:
                    if debugPrint.level >= 4: dp('PlaneOffsetUnion Logic: %s - reducing linear displacement degrees of freedom from 2 to 1' % objName)
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName ) )
                    self.dofs_removed = matches
                    success = True
                    break
            elif len(matches) == 1: 
                vM = self.variableManager
                planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                if abs(dotProduct( planeNormalVector, matches[0].directionVector)) < 10 **-6: #then constraint redudant
                    if debugPrint.level >= 4: dp('PlaneOffsetUnion Logic: %s - planeNormal constraint does not effect remaining dof -> no dof reduction.' % objName)
                    #self.degreesOfFreedom =  dofs
                    #self.dofs_removed = []
                    #success = True
                else:
                    if debugPrint.level >= 4: dp('PlaneOffsetUnion Logic: %s - reducing linear displacement degrees of freedom from 1 to 0' % objName)
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.dofs_removed = matches
                    success = True
                    break
         
        if success:
            self.updateDegreesOfFreedomAnalytically()
        return success
        #if not success:
        #    raise NotImplementedError, 'Panic! PlaneOffsetUnion Logic not programmed for the reduction of degrees of freedom of:\n%s' % '\n'.join(d.str('  ') for d in dofs )

        
    def updateDegreesOfFreedomAnalytically( self ):
        vM = self.variableManager
        planeNormalVector = vM.rotate( self.obj1Name, self.a1_r, vM.X )
        if len(self.dofs_removed) == 3:
            d1,d2 = plane_degrees_of_freedom(planeNormalVector)
            self.degreesOfFreedom[-2].setDirection( d1)
            self.degreesOfFreedom[-1].setDirection( d2)
        elif len(self.dofs_removed) == 2:
            c = crossProduct( self.dofs_removed[0].directionVector, self.dofs_removed[1].directionVector)
            planeNormalMatches = c/norm(c) #plane of self.dofs_removed
            d = planeIntersection( planeNormalVector, planeNormalMatches )
            self.degreesOfFreedom[-1].setDirection(d)
        elif len(self.dofs_removed) < 2: #then object fixed, or constraint redundant.
            pass
        else:
            raise NotImplemented

class AxisDistanceUnion(ConstraintSystemPrototype):
    label = 'AxisDistanceUnion'
    solveConstraintEq_tol = 10**-5
    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.a1_r =   vM.rotateUndo( self.obj1Name, self.getAxis(self.obj1Name, self.subElement1), vM.X0 )
        self.a2_r =   vM.rotateUndo( self.obj2Name, self.getAxis(self.obj2Name, self.subElement2), vM.X0 )
        self.pos1_r = vM.rotateAndMoveUndo( self.obj1Name, self.getPos(self.obj1Name, self.subElement1), vM.X0 )
        self.pos2_r = vM.rotateAndMoveUndo( self.obj2Name, self.getPos(self.obj2Name, self.subElement2), vM.X0 )

    def constraintEq_value( self, X ):
        vM = self.variableManager
        a1 = vM.rotate( self.obj1Name, self.a1_r, X )
        a2 = vM.rotate( self.obj2Name, self.a2_r, X )
        pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, X )
        pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, X )
        # dist = distance_between_axes( pos1, a1, pos2, a2 )
        #   is numerically unstable creating problems, and 
        # dist = distance_between_two_axes_3_points( pos1, a1, pos2, a2 )
        #   is sensitive to axis misalignment, which is should not be because, axis alignment should be taken care of in the axis alignment constraint. Therefore
        dist = distance_between_axis_and_point( pos1, a1, pos2 )
        if numpy.isnan(dist):
            if debugPrint.level >= 1: dp('numpy.isnan(dist)')
            if debugPrint.level >= 1: dp('  locals %s' % formatDictionary(locals(),' '*6) )
            if debugPrint.level >= 1: dp('  %s.__dict %s' % (self.label, formatDictionary( self.__dict__,' '*6 ) ) )   
            raise ValueError, ' assembly2 AxisDistanceUnion numpy.isnan(dist) check console for details'
        return dist - self.constraintValue

    def analyticalSolution(self):
        if  self.constraintValue == 0:
            D = self.solveConstraintEq_dofs #degrees of freedom
            for objName in [self.obj1Name, self.obj2Name]:
                matches = [d for d in D if d.objName == objName and not d.rotational() ]
                if len(matches) > 0:
                    if debugPrint.level >= 4: dp('    %s %s has linear displacement degrees of freedom, checking for analyticalSolution.'% (self.label, objName))
                    vM = self.variableManager
                    a = vM.rotate( self.obj1Name, self.a1_r, vM.X )
                    pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, vM.X )
                    pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, vM.X )
                    error_v =  (pos1-pos2) - dotProduct(a,pos1-pos2)*a
                    a_v = normalize(error_v)
                    error =  norm( error_v ) - self.constraintValue
                    requiredDisp = a_v*error
                    if objName == self.obj1Name:
                        requiredDisp = -requiredDisp
                    if debugPrint.level >= 4: dp('    requiredDisp %s' % requiredDisp )
                    V = [ dot( m.directionVector, requiredDisp ) for m in matches ]
                    #for m,v in zip(matches,V):
                    #    print(m,v)
                    #debugPrint(4,str(V))
                    actualDisp = sum( v*m.directionVector for m,v in zip(matches,V) )
                    if abs(dot(a_v,requiredDisp) - dot(a_v,actualDisp)) < 10**-9:
                        if debugPrint.level >= 3: dp('    %s analyticalSolution available by moving %s.'% (self.label, objName))
                        for m,v in zip(matches,V):
                            m.setValue( m.getValue() + v  )
                        self.parentSystem.update() 
                        self.sys2.update()
                        return True
        return False


    def generateDegreesOfFreedomAnalytically( self ):
        dofs = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        #first try to look for an object which has 3 linear motion degrees of freedom'
        success = False
        if self.constraintValue <> 0:
            raise NotImplementedError, '%s self.constraintValue <> 0 not implemented yet' % self.label
        vM = self.variableManager
        axisVector = vM.rotate( self.obj1Name, self.a1_r, vM.X )
        self.dof_added = False
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in dofs if d.objName == objName and not d.rotational() ]
            if len(matches) == 3:
                if debugPrint.level >= 4: dp('%s Logic: %s - reducing linear displacement degrees of freedom from 3 to 1' % (self.label, objName))
                self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName) )
                self.dof_added = True
                success = True
                break
            elif len(matches) == 2:
                c = crossProduct( matches[0].directionVector, matches[1].directionVector)
                planeNormalMatches = c/norm(c)
                if abs(dotProduct( axisVector, planeNormalMatches)) < 10 **-6: #then co-planar
                    if debugPrint.level >= 4: dp('%s Logic: %s axis in movement plane, therefore linear degrees of freedom reduced from 2 to 1' % (self.label, objName))
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    self.degreesOfFreedom.append( LinearMotionDegreeOfFreedom( self, objName) )
                    self.dof_added = True
                    success = True
                    break
                else:
                    if debugPrint.level >= 4: dp('%s Logic: %s axis not in movement plane, therefore linear degrees of freedom reduced from 2 to 0' % (self.label, objName))
                    self.degreesOfFreedom =  [ d for d in dofs if not d in matches ]
                    success = True
                    break
            elif len(matches) == 1: 
                if abs(dotProduct(axisVector , matches[0].directionVector)) < 10 **-6: #then constraint redudant
                    if debugPrint.level >= 4: dp('%s Logic: %s - axis movement constraint does not effect remaining dof -> no dof reduction.' % (self.label, objName))
                    #self.degreesOfFreedom =  dofs
                    #success = True
                else:
                    if debugPrint.level >= 4: dp('%s Logic: %s - axis movement constraint different from last linear displacement degree of freedom -> reducing degrees of freedom from 1 to 0' % (self.label, objName))
                    self.degreesOfFreedom = [ d for d in dofs if not d in matches ]
                    success = True
                    break
        #if len(dofs) == 3 and all( isinstance(d, AxisRotationDegreeOfFreedom) for d in dofs ):
        #    self.degreesOfFreedom = [dofs[0]]
        #    debugPrint(0,'WARNING*WARNING*WARNING* forcing solution for 3 bar linkage.')
        #    success = True    
        if success:
            self.updateDegreesOfFreedomAnalytically()
        #if not success:
        #    raise NotImplementedError, 'Panic! %s.generateDegreesOfFreedomAnalytical Logic not programmed for the reduction of degrees of freedom of:\n%s' % ( self.label, '\n'.join(d.str('  ') for d in dofs) )
        return success
        
    def updateDegreesOfFreedomAnalytically( self ):
        if self.dof_added:
            vM = self.variableManager
            axisVector = vM.rotate( self.obj1Name, self.a1_r, vM.X )
            self.degreesOfFreedom[-1].setDirection(axisVector)





class VertexUnion(ConstraintSystemPrototype):
    label = 'VertexUnion'
    def init2(self):
        vM = self.variableManager
        #get rotation r(relative) to objects initial placement.
        self.pos1_r = vM.rotateAndMoveUndo( self.obj1Name, self.getPos(self.obj1Name, self.subElement1), vM.X0 )
        self.pos2_r = vM.rotateAndMoveUndo( self.obj2Name, self.getPos(self.obj2Name, self.subElement2), vM.X0 )
        self.DOF_to_remove = None
        
    def constraintEq_value( self, X ):
        vM = self.variableManager
        pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, X )
        pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, X )
        return norm(pos1 - pos2)

    def analyticalSolution(self):
        D = self.solveConstraintEq_dofs #degrees of freedom
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in D if d.objName == objName and not d.rotational() ]
            if len(matches) > 0 : 
                if debugPrint.level >= 4: dp('    %s %s has linear displacement degrees of freedom, checking for analyticalSolution.'% (self.label, objName))
                vM = self.variableManager
                pos1 = vM.rotateAndMove( self.obj1Name, self.pos1_r, vM.X )
                pos2 = vM.rotateAndMove( self.obj2Name, self.pos2_r, vM.X )
                requiredDisp = pos1 - pos2
                if objName == self.obj1Name:
                    requiredDisp = -requiredDisp
                if debugPrint.level >= 4: dp('    requiredDisp %s' % requiredDisp )
                V = [ dot( m.directionVector, requiredDisp ) for m in matches ]
                #for m,v in zip(matches,V):
                #    print(m,v)
                #debugPrint(4,str(V))
                actualDisp = sum( v*m.directionVector for m,v in zip(matches,V) )
                if norm( requiredDisp - actualDisp) < 10**-9:
                    if debugPrint.level >= 3: dp('    %s analyticalSolution available by moving %s.'% (self.label, objName))
                    for m,v in zip(matches,V):
                        m.setValue( m.getValue() + v  )
                        #print(m)
                    self.DOF_to_remove = matches
                    self.parentSystem.update() # required else degrees of freedom whose systems are more then 1 level up the constraint system tree do not update
                    self.sys2.update()
                    return True

        return False

    def generateDegreesOfFreedomAnalytically( self ):
        D = self.parentSystem.degreesOfFreedom + self.sys2.degreesOfFreedom
        self.degreesOfFreedom = []
        #first try to look for an object which has 3 linear motion degrees of freedom'
        success = False
        for objName in [self.obj1Name, self.obj2Name]:
            matches = [d for d in D if d.objName == objName and not d.rotational() ]
            if len(matches) == 3: #todo somehow add support for 3,2 cases
                if debugPrint.level >= 3: dp('  VertexUnion Logic: %s removing all 3 movement degrees of freedom' % objName )
                self.degreesOfFreedom = [ d for d in D if not d in matches ] 
                success = True
        return success
        #if not success:
        #    raise NotImplementedError, 'Panic! PlaneOffsetUnion Logic not programmed for the reduction of degrees of freedom of:\n%s' % '\n'.join(d.str('  ') for d in dofs )

        
    def updateDegreesOfFreedomAnalytically( self):
        pass

