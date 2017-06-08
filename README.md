FreeCAD_assembly2
=================

Assembly workbench for FreeCAD v0.15, 0.16 and 0.17 with support for importing parts from external files.
Although the original programmer of the workbench (hamish) is no longer active
this workbench is still maintained as good as possible.
Feel free to post issues and pull requests.
Assembly2 requires numpy to be installed (bundled with FreeCAD since 0.15.4671).
Thanks to Maurice (easyw-fc) assembly2 will work with files from FreeCAD 0.17.


Linux Installation Instructions
-------------------------------

For Ubuntu (Linux Mint) we recommend to add the community ppa to your systems software
resources and install via the sysnaptic package manager the addon of your liking.
Refer to here for more information:
https://launchpad.net/~freecad-community/+archive/ubuntu/ppa

On other Linux distros you may try to install manually via BASH and git:

```bash
$ sudo apt-get install git python-numpy python-pyside
$ mkdir ~/.FreeCAD/Mod
$ cd ~/.FreeCAD/Mod
$ git clone https://github.com/hamish2014/FreeCAD_assembly2.git
```

Once installed, use git to easily update to the latest version:

```bash
$ cd ~/.FreeCAD/Mod/FreeCAD_assembly2
$ git pull
$ rm *.pyc
```

Windows Installation Instructions
---------------------------------

Please use the FreeCAD-Addons-Installer provided here:
https://github.com/FreeCAD/FreeCAD-addons

For more in-depth information refer to the corresponding tutorial on the FreeCAD-Homepage:
http://www.freecadweb.org/wiki/index.php?title=How_to_install_additional_workbenches

Mac Installation Instructions
-----------------------------

* download the git repository as ZIP
* assuming FreeCAD is installed in "/Applications/FreeCAD/v 0.15", go to "/Applications/FreeCAD/v 0.15" in the Browser, and select FreeCAD.app
* right-click and select "Show Package Contents", a new window will appear with a folder named "Contents"
* single-click on the folder "Contents" and select the folder "Mod"
* in the folder "Mod" create a new folder named "assembly2"
* unzip downloaded repository in the folder "Contents/Mod/assembly2"
(Thanks piffpoof)


For more in-depth information refer to the corresponding tutorial on the FreeCAD-Homepage:
http://www.freecadweb.org/wiki/index.php?title=How_to_install_additional_workbenches

Wiki
----

For instructions on usage of the workbench refer to the wiki
[link on top of the page](https://github.com/hamish2014/FreeCAD_assembly2/wiki).
