from robofab.interface.all.dialogs import Message as FabMessage
from mojo.roboFont import CurrentFont
from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
from views import TTHProgressWindow
reload(TTHProgressWindow)

def go():
	font = CurrentFont()
	if (font is None) or (not helperFunctions.fontIsQuadratic(font)):
		FabMessage("This is not a Quadratic/TrueType UFO.\nNothing to do.")
		return

	fm = tthTool.fontModelForFont(font)
	if fm is None:
		FabMessage("Can't find the TTHFont instance. Sorry. Bye.")
		return

	exn = None
	pbw = TTHProgressWindow.TTHProgressWindow("Dumping PNGs...", len(font))
	dname = "None"
	try:
		dname = fm.dumpPNGs(pbw)
	except Exception as inst:
		exn = inst
	finally:
		if pbw: pbw.close()
	if exn:
		print "[TTH ERROR] An error happened during the generation of the glyphs' PNG images for font", font.fileName
		print exn
	else:
		print "PNG images shipped into directory:", dname
