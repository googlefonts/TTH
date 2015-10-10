
from robofab.interface.all.dialogs import Message as FabMessage
from robofab.interface.all.dialogs import AskYesNoCancel as AskYesNoCancel

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions

def go():
	font = CurrentFont()
	if (font is None) or (not helperFunctions.fontIsQuadratic(font)):
		FabMessage("This is not a Quadratic/TrueType UFO.\nNothing to clean.")
		return

	choice = AskYesNoCancel('Shall I really clean the TTH data in UFO\n\t{} ?'.format(font.fileName),
			title="TTH",
			default=0,
			informativeText="(You might lose a lot of hard work.)")
	if choice != 1:
		return
	fm = tthTool.fontModelForFont(font)
	if fm is None:
		FabMessage("Can't find the TTHFont instance. Sorry. Bye.")
		return
	try:
		fm.purgeHintingData()
	except Exception as inst:
		print "[TTH ERROR] An error happened during the compilation of the glyphs' hinting program in font", font.fileName
		print exn
		return
	print "TTH data purged from font", font.fileName

go()
