from auto import TransferPanel

if AllFonts() != []:
	if CurrentGlyph() != None:
		OpenWindow(TransferPanel.TransferPanel)
	else:
		print 'Select a Glyph'
else:
	print 'Open UFOs first'