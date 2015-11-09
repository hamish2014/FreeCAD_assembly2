import assembly2lib #QtCore.QResource.registerResource happens in assembly2lib

class Assembly2Workbench (Workbench): 
    MenuText = 'Assembly 2'
    def Initialize(self):
        import axialConstraint, assembly2solver, importPart, planeConstraint, circularEdgeConstraint, muxAssembly, angleConstraint, partsList, degreesOfFreedomAnimation, sphericalSurfaceConstraint, checkAssembly, boltMultipleCircularEdges
        commandslist = [
            'importPart', 
            'updateImportedPartsCommand', 
            'assembly2_movePart', 
            'addCircularEdgeConstraint', 
            'addPlaneConstraint', 
            'addAxialConstraint', 
            'addAngleConstraint', 
            'addSphericalSurfaceConstraint',
            'boltMultipleCircularEdges',
            'degreesOfFreedomAnimation', 
            'assembly2SolveConstraints',
            'muxAssembly',
            'addPartsList',
            'assembly2_checkAssembly'
            ]
        self.appendToolbar('Assembly 2', commandslist)
        self.treecmdList = ['importPart', 'updateImportedPartsCommand']
        FreeCADGui.addIconPath( ':/assembly2/icons' )
        FreeCADGui.addPreferencePage( ':/assembly2/ui/assembly2_prefs.ui','Assembly2' )
        self.appendMenu('Assembly 2', commandslist)

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
                if 'ConstraintInfo' in obj.Content or 'ConstraintNfo' in obj.Content:
                    redefineCmd = {
                        'plane':'redefinePlaneConstraint',
                        'angle_between_planes':'redefineAngleConstraint',
                        'axial': 'redefineAxialConstraint',
                        'circularEdge' : 'redefineCircularEdgeConstraint',
                        'sphericalSurface' : 'redefineSphericalSurfaceConstraint'
                        }[ obj.Type ]
                    self.appendContextMenu( "Assembly2", [redefineCmd,'selectConstraintObjects','selectConstraintElements'])
                if 'sourceFile' in  obj.Content:
                    self.appendContextMenu( "Assembly2", 
                        ['assembly2_movePart',
                         'assembly2_duplicatePart',
                         'assembly2_editImportedPart',
                         'assembly2_forkImportedPart',
                         'assembly2_deletePartsConstraints'])

    Icon = ':/assembly2/icons/workBenchIcon.svg'

Gui.addWorkbench(Assembly2Workbench())
