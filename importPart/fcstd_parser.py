'''
Used instead of openning document via FreeCAD.openDocument

Info on the FreeCAD file format:
https://www.freecadweb.org/wiki/index.php?title=File_Format_FCStd
'''

import FreeCAD
import Part #from FreeCAD
import os
import numpy
from zipfile import ZipFile
import xml.etree.ElementTree as XML_Tree

def xml_prettify( xml_str ):
    import xml.dom.minidom as minidom
    xml = minidom.parseString( xml_str )
    S = xml.toprettyxml(indent='  ')
    return '\n'.join( s for s in S.split('\n') if s.strip() != '' )

class Fcstd_File_Parser:
    '''
    https://www.freecadweb.org/wiki/index.php?title=File_Format_FCStd
    Each object, even if it is parametric, has its shape stored as an individual .brep file, so it can be accessed by components without the need to recalculate the shape. 
    '''
    def __init__(
            self,
            fn,
            only_load_visible_shapes = True,
            visible_if_ViewObject_missing = True,
            printLevel=0
    ):
        z = ZipFile( fn )
        if printLevel > 0:
            print( z.namelist() )
            print( xml_prettify( z.open('Document.xml').read() ) )
            if 'GuiDocument.xml' in z.namelist():
                print( xml_prettify( z.open('GuiDocument.xml').read() ) )
        tree_doc = XML_Tree.fromstring(  z.open('Document.xml').read() )
        if 'GuiDocument.xml' in z.namelist():
            tree_gui = XML_Tree.fromstring(  z.open('GuiDocument.xml').read() )
        else:
            tree_gui = None
        #tree_shapes =  ElementTree.fromstring(  z.open('PartShape.brp').read() )
        doc = Fcstd_Property_List( tree_doc.find('Properties') )
        self.__dict__.update( doc.__dict__ )
        self.Name = os.path.split( fn )[1][:-6]
        self.Objects = []
        self.Objects_dict = {}
        #objectData
        for o in tree_doc.find('ObjectData').findall('Object'):
            k = o.attrib['name']
            assert not k in self.Objects
            obj = Fcstd_Property_List( o.find('Properties') )
            obj.Name = k
            obj.Content = XML_Tree.tostring( o )
            self.Objects_dict[k] = obj
            self.Objects.append( self.Objects_dict[k] )
        #viewObjects
        if tree_gui != None:
            for o in tree_gui.find('ViewProviderData').findall('ViewProvider'):
                k = o.attrib['name']
                if k in self.Objects_dict:
                    ViewObject =  Fcstd_Property_List( o.find('Properties') )
                    ViewObject.isVisible = isVisible_Bound_Method( ViewObject )
                    self.Objects_dict[k].ViewObject = ViewObject
        else:
            for obj in self.Objects:
                xml = '<Properties> <Property name="Visibility" type="App::PropertyBool"> <Bool value="%s"/> </Property> </Properties>' % ( 'true' if visible_if_ViewObject_missing else 'false' )
                obj.ViewObject =  Fcstd_Property_List(  XML_Tree.fromstring(xml) )
                obj.ViewObject.isVisible = isVisible_Bound_Method( obj.ViewObject )
        #shapes
        for obj in self.Objects:
            if hasattr( obj, 'Shape'):
                shape_zip_name = obj.Shape
                delattr( obj, 'Shape' )
                if not only_load_visible_shapes or obj.ViewObject.Visibility:
                    obj.Shape = Part.Shape()
                    obj.Shape.importBrepFromString( z.open( shape_zip_name ).read() )
        #colour lists
        for obj in self.Objects:
            if hasattr( obj, 'ViewObject' ):
                v = obj.ViewObject
                if not only_load_visible_shapes or obj.ViewObject.Visibility:
                    for p_name, p_type in zip( v.PropertiesList, v.PropertiesTypes ):
                        if p_type == 'App::PropertyColorList':
                            #print( p_name, getattr(v,p_name) )
                            fn = getattr(v,p_name)
                            C = parse_Clr_Array(  z.open( fn ).read() )
                            setattr(  v, p_name, C )
                    

class isVisible_Bound_Method:
    def __init__( self, ViewObject_Property_List ):
        self.Properties = ViewObject_Property_List
    def __call__( self ):
        return self.Properties.Visibility


class Fcstd_Property_List:
    def __init__( self, Properties_XML_Tree ):
        self.PropertiesList = []
        self.PropertiesTypes = []
        for p in Properties_XML_Tree.findall('Property'):
            #print(  XML_Tree.tostring( p ).strip() )
            name = p.attrib['name']
            p_type = p.attrib['type']
            if p_type == 'App::PropertyMaterial':
                continue # not implemented yet
            #print(  XML_Tree.tostring( p ).strip() )
            #print( len(p) )
            if len( p ) == 1:
                #print(p[0].tag)
                if p[0].tag == 'Bool':
                    v = p[0].attrib['value'] == 'true'
                elif p[0].tag == 'Float':
                    v = float(p[0].attrib['value'])
                elif p[0].tag == 'Integer' or p_type in ("App::PropertyPercent"):
                    v = int(p[0].attrib['value'])
                elif p_type == "App::PropertyColor":
                    v = parse_App_PropertyColor(p[0].attrib['value'])
                elif p_type == "App::PropertyPlacement":
                    v = App_PropertyPlacement( p[0] )
                else:
                    v = p[0].attrib[ p[0].keys()[0]]
                self.addProperty( name, p_type, v )
                #print(name,v)
            elif p_type == "App::PropertyEnumeration":
                #print( XML_Tree.tostring( p ) )
                ind = int(p[0].attrib['value'])
                self.addProperty( name, p_type, p[1][ind].attrib['value'] )
            else:
                FreeCAD.Console.PrintWarning( 'unable to parse\n  %s \nsince more than 1 childern\n' % (XML_Tree.tostring( p )) )
    def addProperty( self, name, p_type, value ):
         assert not hasattr(self, name)
         setattr(self, name, value)
         self.PropertiesList.append( name )
         self.PropertiesTypes.append( p_type )

class App_PropertyPlacement:
    def __init__( self, property_xml ):
        #print( XML_Tree.tostring( property_xml ) )
        self.Base = App_PropertyPlacement_Base( property_xml )
        self.Rotation = App_PropertyPlacement_Rotation( property_xml )
class App_PropertyPlacement_Base:
    def __init__( self, p ):
        self.x = float( p.attrib['Px'] )
        self.y = float( p.attrib['Py'] )
        self.z = float( p.attrib['Pz'] )
class App_PropertyPlacement_Rotation:
    def __init__( self, p ):
        self.Q = [ float(p.attrib[k]) for k in ('Q0','Q1','Q2','Q3') ]
        

def parse_App_PropertyColor( t ):
    '''
    written as a workaround for the 
    'type must be int or tuple of float, not tuple'
    error, which does not accept ints
    '''
    c =  int( t )
    V = [
        (c / 16777216 ) % 256,
        (c / 65536 ) % 256,
        (c / 256   ) % 256, 
        c % 256,
    ]
    return tuple( numpy.array( V, dtype='float64' ) / 255 )

def parse_Clr_Array( fileContent ):
    C = numpy.fromstring( fileContent, dtype=numpy.uint32 )
    n = C[0]
    assert len(C) == n + 1
    return [  parse_App_PropertyColor(c) for c in C[1:] ]

        

#testing done in importPart/tests.py
