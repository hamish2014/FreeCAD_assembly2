
class Assembly2Workbench (Workbench): 
    import os
    from assembly2lib import __dir__
    Icon = os.path.join( __dir__ , 'workBenchIcon.svg' )
    MenuText = "Assembly 2"
    def Initialize(self):
        from assembly2lib import __dir__
        import axialConstraint, assembly2solver, importPart, planeConstraint, circularEdgeConstraint, muxAssembly
        commandslist = ["importPart", "updateImportedPartsCommand", "addCircularEdgeConstraint", "addPlaneConstraint", "addAxialConstraint", "assembly2SolveConstraints","muxAssembly"]
        self.appendToolbar("Assembly 2", commandslist)

Gui.addWorkbench(Assembly2Workbench())
