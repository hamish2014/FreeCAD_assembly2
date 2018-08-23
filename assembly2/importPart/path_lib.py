import os, posixpath, ntpath

def path_split( pathLib, path):
    parentPath, childPath = pathLib.split( path )
    parts = [childPath]
    while childPath != '':
        parentPath, childPath = pathLib.split( parentPath )
        parts.insert(0, childPath)
    parts[0] = parentPath
    if  pathLib == ntpath and parts[0].endswith(':/'): #ntpath ...
        parts[0] = parts[0][:-2] + ':\\'
    return parts

def path_join( pathLib, parts):
    if pathLib == posixpath and parts[0].endswith(':\\'):
        path = parts[0][:-2]+ ':/'
    else:
        path = parts[0]
    for part in parts[1:]:
        path = pathLib.join( path, part)
    return path

def path_convert( path, pathLibFrom, pathLibTo):
    parts =  path_split( pathLibFrom, path)
    return path_join(pathLibTo, parts )

def path_rel_to_abs(path):
    j = FreeCAD.ActiveDocument.FileName.rfind('/')
    k = path.find('/')
    absPath = FreeCAD.ActiveDocument.FileName[:j] + path[k:]
    FreeCAD.Console.PrintMessage("First %s\n" % FreeCAD.ActiveDocument.FileName[:j])
    FreeCAD.Console.PrintMessage("Next %s\n" % path[k:])
    FreeCAD.Console.PrintMessage("absolutePath is %s\n" % absPath)
    if path.startswith('.') and os.path.exists( absPath ):
        return absPath
    else:
        return None

