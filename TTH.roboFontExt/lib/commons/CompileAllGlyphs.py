
from robofab.interface.all.dialogs import Message as FabMessage

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
from views import TTHProgressWindow
reload(TTHProgressWindow)

def go():
	font = CurrentFont()
	if (font is None) or (not helperFunctions.fontIsQuadratic(font)):
		FabMessage("This is not a Quadratic/TrueType UFO.\nNothing to do.")
		return
	exn = None
	fm = tthTool.fontModelForFont(font)
	pbw = TTHProgressWindow.TTHProgressWindow("Compiling all glyphs...", len(font)+60)
	try:
		fm.compileAllTTFData(pbw)
	except Exception as inst:
		exn = inst
	finally:
		if pbw: pbw.close()
	if exn:
		print "[TTH ERROR] An error happened during the compilation of the glyphs' hinting program in font", font.fileName
		print exn
	else:
		print "TTH data compiled for font", font.fileName

go()
