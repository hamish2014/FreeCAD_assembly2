
class Assembly2Workbench (Workbench): 
    MenuText = 'Assembly 2'
    def Initialize(self):
        from assembly2lib import __dir__
        import axialConstraint, assembly2solver, importPart, planeConstraint, circularEdgeConstraint, muxAssembly, angleConstraint, partsList, degreesOfFreedomAnimation, sphericalSurfaceConstraint
        commandslist = [
            'importPart', 
            'updateImportedPartsCommand', 
            'assembly2_movePart', 
            'addCircularEdgeConstraint', 
            'addPlaneConstraint', 
            'addAxialConstraint', 
            'addAngleConstraint', 
            'addSphericalSurfaceConstraint',
            'degreesOfFreedomAnimation', 
            'assembly2SolveConstraints',
            'muxAssembly',
            'addPartsList'
            ]
        self.appendToolbar('Assembly 2', commandslist)
        self.treecmdList = ['importPart', 'updateImportedPartsCommand']
        #self.appendMenu('Assembly 2', commandslist)

    def Activated(self):
        from assembly2lib import FreeCAD, updateOldStyleConstraintProperties
        doc = FreeCAD.activeDocument()
        if hasattr(doc, 'Objects'):
            updateOldStyleConstraintProperties(doc)

    def ContextMenu(self, recipient):
        selection = [s  for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        if len(selection) == 1:
            obj = selection[0]
            if hasattr(obj,'Content'):
                if 'ConstraintInfo' in obj.Content:
                    redefineCmd = {
                        'plane':'redefinePlaneConstraint',
                        'angle_between_planes':'redefineAngleConstraint',
                        'axial': 'redefineAxialConstraint',
                        'circularEdge' : 'redefineCircularEdgeConstraint',
                        'sphericalSurface' : 'redefineSphericalSurfaceConstraint'
                        }[ obj.Type ]
                    self.appendContextMenu( "Assembly2", [redefineCmd,'selectConstraintObjects'])
                if 'sourceFile' in  obj.Content:
                    self.appendContextMenu( "Assembly2", 
                        ['assembly2_movePart',
                         'assembly2_duplicatePart',
                         'assembly2_editImportedPart',
                         'assembly2_forkImportedPart',
                         'assembly2_deletePartsConstraints'])

    # Icon generated using by converting svg to xpm format using Gimp
    Icon = '''
/* XPM */
static char * workBenchIcon_xpm[] = {
"32 32 27 1",
"       c None",
".      c #000003",
"+      c #000000",
"@      c #000009",
"#      c #00066A",
"$      c #000BCE",
"%      c #000004",
"&      c #000883",
"*      c #000EFF",
"=      c #000005",
"-      c #000564",
";      c #000BC1",
">      c #000449",
",      c #000896",
"'      c #000006",
")      c #000442",
"!      c #00099F",
"~      c #000112",
"{      c #00087C",
"]      c #00010A",
"^      c #000669",
"/      c #00011C",
"(      c #000879",
"_      c #000EF8",
":      c #000563",
"<      c #000DEF",
"[      c #00011A",
".+++++++++++++++                ",
"@#$$$$$$$$$$$$$%                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@&*************=                ",
"@-;;;;;;;;;;;;;%                ",
".+++++++++++++++                ",
".==============.................",
"@>,,,,,,,,,,,,,'=)!!!!!!!!!!!!!~",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@{*************]=^*************/",
"@(_____________]=:<<<<<<<<<<<<<[",
"%+++++++++++++++.+++++++++++++++"};
'''


Gui.addWorkbench(Assembly2Workbench())
