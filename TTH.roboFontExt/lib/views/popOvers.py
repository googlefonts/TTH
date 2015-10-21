
from AppKit import NSImage, NSImageNameRightFacingTriangleTemplate, NSImageNameLeftFacingTriangleTemplate
from vanilla import Popover, CheckBox, TextBox, Slider, ComboBox, PopUpButton, ImageButton
from mojo.events import getActiveEventTool
from commons import helperFunctions as HF
from models.TTHTool import uniqueInstance as tthTool

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  C O N S T A N T S
#
#  Some of these might be fruitfully moved somewhere else
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# For display in a [popup] menu
gAlignmentUINameList = ['Closest Pixel Edge',
				'Left/Bottom Edge',
				'Right/Top Edge',
				'Center of Pixel',
				'Double Grid']
gAlignmentWithNoneUINameList = ['Do Not Align to Grid'] + gAlignmentUINameList
# For internal use
gAlignmentTypeList   = ['round',
				'left',
				'right',
				'center',
				'double']
gAlignmentWithNoneTypeList   = ['None'] + gAlignmentTypeList
# Reverse direction, from string in the lists above, to the index of the element
gAlignTypeToIndex         = HF.makeListItemToIndexDict(gAlignmentTypeList)
gAlignWithNoneTypeToIndex = HF.makeListItemToIndexDict(gAlignmentWithNoneTypeList)

# Images used in the widget for moving the points involved in a command
gImgNext = NSImage.imageNamed_(NSImageNameRightFacingTriangleTemplate)
gImgNext.setSize_((8, 8))
gImgPrev = NSImage.imageNamed_(NSImageNameLeftFacingTriangleTemplate)
gImgPrev.setSize_((8, 8))

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  U T I L I T Y   F U N C T I O N S
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def makeEmptyPopover(size, pos, view):
	'''Creates a vanilla.Popover with given size and position, and gives it a
	basic debug'''
	p = Popover(size)
	if not hasattr(p, "_bindings"):
		p._bindings = {}
	offsetX, offsetY = view.offset()
	return (p, (pos.x+offsetX, pos.y+offsetY))

def makeStemsLists():
	x = ['None']
	y = ['None']
	fm = tthTool.getFontModel()
	x.extend(fm.verticalStems.keys())
	y.extend(fm.horizontalStems.keys())
	return x, y

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  C A L L B A C K   C L A S S E S
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class PopoverPointMoverCallback(object):
	'''A callback used in several popovers. Used to move the point named
	cmd.get(key) in the cmd, either forward or backward along the contours'''
	def __init__(self, popoC, cmd, key, forward):
		self.popoverController = popoC
		self.cmd = cmd
		self.key = key
		self.forward = forward

	def __call__(self, sender):
		gm = self.popoverController.gm
		fm = self.popoverController.fm
		csi = gm.csiOfPointName(self.cmd.get(self.key))
		alsoOff = 'delta' in self.cmd.get('code')
		if self.forward:
			csi = gm.increaseCSI(csi, alsoOff)
		else:
			csi = gm.decreaseCSI(csi, alsoOff)
		self.cmd.set(self.key, gm.pointOfCSI(csi).name)
		gm.updateGlyphProgram(fm)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  T T H   C O M M A N D   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class TTHCommandPopover(object):
	'''Base class for popovers that are used to edit hinting commands.'''
	def __init__(self, gm, fm, cmd, size, point):
		eventTool = getActiveEventTool()
		p,v              = makeEmptyPopover(size, point, eventTool.getNSView())
		p.controller     = self
		self.gm          = gm
		self.fm          = fm
		self._cmd        = cmd
		self._popover    = p
		self._viewPos    = v
		p.bind("did show", eventTool.popoverOpened)
		p.bind("did close", eventTool.popoverClosed)

	@property
	def relativeRect(self):
		x,y = self._viewPos
		return (x-2, y-2, 4, 4)

	@property
	def popover(self):
		return self._popover

	@property
	def cmd(self):
		return self._cmd

	def close(self):
		self.popover.close()

	def open(self):
		self.popover.open(parentView=getActiveEventTool().getNSView(), relativeRect=self.relativeRect)

	def setupStateUI(self):
		popo = self.popover
		popo.stateCheckBox = CheckBox((-23, 8, 22, 22), "", callback=self.stateCheckBoxCallback, sizeStyle='small')
		popo.stateCheckBox.set(self.cmd.get('active') == 'true')
		popo.stateTitle = TextBox((10, 14, -30, 17), 'Active', sizeStyle='small')

	def stateCheckBoxCallback(self, senderCheckBox):
		if senderCheckBox.get() == 0:
			# FIXME: is it of any use to prepare undo stuff while the RGlyph will not change?
			# It might be better to do that on TTHGLyph, if we implement support for undo in it
			self.gm.prepareUndo("Deactivate Command")
			self.cmd.set('active', 'false')
		else:
			self.gm.prepareUndo("Activate Command")
			self.cmd.set('active', 'true')
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	def setupPointMoverUI(self, pos, key, label, labelLeft=72, labelWidth=60):
		prevCB = PopoverPointMoverCallback(self, self.cmd, key, False)
		nextCB = PopoverPointMoverCallback(self, self.cmd, key, True)
		self.popover.__setattr__("prevButton"+key,\
			ImageButton((10, pos, 10, 10), imageObject=gImgPrev, bordered=False,\
			callback=prevCB, sizeStyle='small'))
		self.popover.__setattr__("nextButton"+key,\
			ImageButton((-20, pos, 10, 10), imageObject=gImgNext, bordered=False,\
			callback=nextCB, sizeStyle='small'))
		self.popover.__setattr__("movePointText"+key, \
				TextBox((labelLeft, pos-2, labelWidth, 15), label, sizeStyle = "small"))

	def setupAlignmentTypeUI(self, height, withNone = True, show = True):
		if withNone:
			uiList = gAlignmentWithNoneUINameList
			self.alignmentTypeList = gAlignmentWithNoneTypeList
		else:
			uiList = gAlignmentUINameList
			self.alignmentTypeList = gAlignmentTypeList
		self.popover.alignmentTypeText = TextBox((10, height, 40, 15), "Align:", sizeStyle = "small")
		self.popover.alignmentTypePopUpButton = PopUpButton((50, height-2, -10, 16),
				uiList, sizeStyle = "mini",
				callback=self.alignmentTypePopUpButtonCallback)

		self.popover.alignmentTypeText.show(show)
		self.popover.alignmentTypePopUpButton.show(show)

	def alignmentTypePopUpButtonCallback(self, senderPopup):
		self.gm.prepareUndo('Change Alignment')
		selected = self.alignmentTypeList[senderPopup.get()]
		self.cmd.set('align', selected)
		if selected == 'None':
			HF.delCommandAttrib(self.cmd, 'align')
		HF.delCommandAttrib(self.cmd, 'round')
		HF.delCommandAttrib(self.cmd, 'stem')
		if self.cmd.get('code') in ['alignt', 'alignb']:
			self.cmd.set('code', 'alignv')
			HF.delCommandAttrib(self.cmd, 'zone')
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	def setupRoundDistanceUI(self):
		self.popover.RoundDistanceText = TextBox((10, 32, 80, 15), "Round Distance:", sizeStyle = "small")
		self.popover.RoundDistanceCheckBox = CheckBox((-23, 26, 22, 22), "", sizeStyle = "small",
				callback=self.roundDistanceCheckBoxCallback)
		self.popover.RoundDistanceCheckBox.set(HF.commandHasAttrib(self.cmd, 'round'))

	def roundDistanceCheckBoxCallback(self, sender):
		IAmSinglePopover = hasattr(self.popover, 'alignmentTypePopUpButton')
		if sender.get() == 1:
			self.gm.prepareUndo('Round Distance')
			self.cmd.set('round', 'true')
			HF.delCommandAttrib(self.cmd, 'stem')
			HF.delCommandAttrib(self.cmd, 'align')
		else:
			self.gm.prepareUndo('Do Not Round Distance')
			HF.delCommandAttrib(self.cmd, 'round')
			idx      = self.popover.StemTypePopUpButton.get()
			stemName = self.stemTypeList[idx]
			if stemName != 'None':
				self.cmd.set('stem', stemName)
			elif IAmSinglePopover:
				alignType = self.alignmentTypeList[self.popover.alignmentTypePopUpButton.get()]
				if alignType != 'None':
					self.cmd.set('align', alignType)

		noRound = not HF.commandHasAttrib(self.cmd, 'round')
		noStem  = not HF.commandHasAttrib(self.cmd, 'stem')
		self.popover.StemTypePopUpButton.enable(noRound)
		if IAmSinglePopover:
			self.popover.alignmentTypePopUpButton.enable(noRound and noStem)
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	def findStemIndex(self):
		stemName = self.cmd.get('stem', 'None')
		return self.stemToIndex[stemName]

	def setupStemTypeUI(self):
		self.popover.StemTypeText = TextBox((10, 52, 40, 15), "Stem:", sizeStyle = "small")
		self.popover.StemTypePopUpButton = PopUpButton((50, 50, -10, 16),
				self.stemTypeList, sizeStyle = "mini",
				callback=self.stemTypePopUpButtonCallback)
		self.popover.StemTypePopUpButton.set(self.findStemIndex())
		self.popover.StemTypePopUpButton.enable('round' not in self.cmd)

	def stemTypePopUpButtonCallback(self, sender):
		self.gm.prepareUndo('Change Stem')
		IAmSinglePopover = hasattr(self.popover, 'alignmentTypePopUpButton')
		if sender.get() != 0:
			self.cmd.set('stem', self.stemTypeList[sender.get()])
		else:
			HF.delCommandAttrib(self.cmd, 'stem')
			if IAmSinglePopover:
				alignType = self.alignmentTypeList[self.popover.alignmentTypePopUpButton.get()]
				if alignType != 'None':
					self.cmd.set('align', alignType)

		if IAmSinglePopover:
			noRound = not HF.commandHasAttrib(self.cmd, 'round')
			noStem  = not HF.commandHasAttrib(self.cmd, 'stem')
			self.popover.alignmentTypePopUpButton.enable(noRound and noStem)
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  S I M P L E   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SimplePopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, cmd):
		super(SimplePopover, self).__init__(gm, fm, cmd, (100,100), point)
		self.setupStateUI()
		self.open()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  A L I G N   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class AlignPopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, cmd):
		super(AlignPopover, self).__init__(gm, fm, cmd, (200,110), point)

		popover = self.popover

		self.setupStateUI()
		fm = tthTool.getFontModel()
		self.zonesListItems = fm.zones.keys()

		code = cmd.get('code')

		if code[-1] != 'h':
			popover.zoneTitle = TextBox((10, 34, -30, 20), 'Align to Zone', sizeStyle='small')
			popover.zoneCheckBox = CheckBox((-23, 28, 22, 22), "", callback=self.zoneCheckBoxCallback, sizeStyle='small')
			popover.zoneCheckBox.set(code in ['alignt', 'alignb'])

		self.setupAlignmentTypeUI(height=57, withNone=False, show=False)

		popover.alignmentZoneText = TextBox((10, 57, 40, 15), "Zone:", sizeStyle = "small")
		popover.alignmentZonePopUpButton = PopUpButton((50, 55, -10, 16),
				self.zonesListItems, sizeStyle = "mini",
				callback=self.alignmentZonePopUpButtonCallback)

		popover.alignmentZoneText.show(False)
		popover.alignmentZonePopUpButton.show(False)

		if code in ['alignv', 'alignh']:
			popover.alignmentTypeText.show(True)
			popover.alignmentTypePopUpButton.show(True)
			popover.alignmentTypePopUpButton.set(gAlignTypeToIndex[cmd.get('align')])

		if code in ['alignt', 'alignb']:
			popover.alignmentZoneText.show(True)
			popover.alignmentZonePopUpButton.show(True)
			for index, zone in enumerate(self.zonesListItems):
				if cmd.get('zone') == zone:
					popover.alignmentZonePopUpButton.set(index)
					break

		self.setupPointMoverUI(-20, 'point', 'Move Point')
		self.open()

	def zoneCheckBoxCallback(self, sender):
		if self.zonesListItems == []:
			sender.set(0)
			return
		if sender.get() == 1:
			self.gm.prepareUndo("Align to Zone")
			use_type = False # so, we use zones
			zoneName = self.zonesListItems[0]
			self.handleZone(zoneName)
		else:
			self.gm.prepareUndo("Do Not Align to Zone")
			use_type = True
			self.cmd.set('align', 'round')
			HF.delCommandAttrib(self.cmd, 'zone')
			if tthTool.selectedAxis == 'X':
				self.cmd.set('code', 'alignh')
			else:
				self.cmd.set('code', 'alignv')

		self.popover.alignmentZonePopUpButton.set(0)
		self.popover.alignmentTypePopUpButton.set(0)
		self.popover.alignmentTypeText.show(use_type)
		self.popover.alignmentTypePopUpButton.show(use_type)
		self.popover.alignmentZoneText.show(not use_type)
		self.popover.alignmentZonePopUpButton.show(not use_type)
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	def handleZone(self, zoneName):
		fm = tthTool.getFontModel()
		zones = fm.zones
		code = 'alignb'
		if 'top' in zones[zoneName]:
			if zones[zoneName]['top']:
				code = 'alignt'
		self.cmd.set('code', code)
		self.cmd.set('zone', zoneName)
		HF.delCommandAttrib(self.cmd, 'align')

	def alignmentZonePopUpButtonCallback(self, sender):
		self.gm.prepareUndo('Change Zone')
		zoneName = self.zonesListItems[sender.get()]
		self.handleZone(zoneName)
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  D E L T A   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class DeltaPopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, cmd):
		super(DeltaPopover, self).__init__(gm, fm, cmd, (200,160), point)

		popover = self.popover

		self.setupStateUI()

		PPMSizesList = [str(i) for i in range(9, 73)]

		popover.DeltaRangeText = TextBox((10, 32, 40, 15), "Range:", sizeStyle = "small")
		popover.DeltaRange1ComboBox = ComboBox((-80, 30, 33, 15), PPMSizesList, sizeStyle = "mini",
			callback = DeltaPopover.DeltaRangeComboBoxCallback(self, cmd, firstLimit=True))
		popover.DeltaRange2ComboBox = ComboBox((-43, 30, 33, 15), PPMSizesList, sizeStyle = "mini",
			callback = DeltaPopover.DeltaRangeComboBoxCallback(self, cmd, firstLimit=False))
		popover.DeltaRange1ComboBox.set(str(self.cmd.get('ppm1')))
		popover.DeltaRange2ComboBox.set(str(self.cmd.get('ppm2')))

		popover.DeltaOffsetText = TextBox((10, 50, 50, 15), "Offset:", sizeStyle = "small")
		popover.DeltaOffsetSlider = Slider((10, 65, -10, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
			callback=self.DeltaOffsetSliderCallback)
		popover.DeltaOffsetSlider.set(int(self.cmd.get('delta')) + 8)

		popover.monoTitle = TextBox((10, 90, -30, 20), 'Monochrome', sizeStyle='small')
		popover.monoCheckBox = CheckBox((-23, 84, 22, 22), "", callback=self.MonoCheckBoxCallback, sizeStyle='small')
		popover.monoCheckBox.set(self.cmd.get('mono') == 'true')

		popover.grayTitle = TextBox((10, 110, -30, 20), 'Grayscale & Subpixel', sizeStyle='small')
		popover.grayCheckBox = CheckBox((-23, 104, 22, 22), "", callback=self.GrayCheckBoxCallback, sizeStyle='small')
		popover.grayCheckBox.set(self.cmd.get('gray') == 'true')

		self.setupPointMoverUI(-20, 'point', 'Move Point')
		self.open()

	def close(self):
		self.removeCommandIfNeeded()
		super(DeltaPopover, self).close()

	def removeCommandIfNeeded(self):
		# If the delta is zero upon closing the popover, then we delete the
		# command:
		if int(self.cmd.get('delta')) != 0: return
		print "DeltaPopover closed: delta = 0 ==> deleting the command"
		self.gm.prepareUndo('Remove Delta')
		self.gm.removeHintingCommand(self.cmd)
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	def DeltaOffsetSliderCallback(self, sender):
		newValue = max(-8, min(8, int(sender.get() - 8)))
		if newValue == 0:
			oldValue = int(self.cmd.get('delta'))
			self.popover.DeltaOffsetSlider.set(oldValue+8)
			return
		self.gm.prepareUndo('Change Delta Offset')
		if newValue == 0: # should never happen due to the test above
			self.cmd.set('active', 'false')
		else:
			self.cmd.set('active', 'true')
		self.cmd.set('delta', str(newValue))
		if self.cmd.get('code')[0] == 'm':
			tthTool.changeDeltaOffset('Middle Delta', newValue)
		else:
			tthTool.changeDeltaOffset('Final Delta', newValue)
		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	class DeltaRangeComboBoxCallback(object):
		def __init__(self, popoC, cmd, firstLimit):
			self.popoverController = popoC
			self.cmd = cmd
			self.firstLimit = firstLimit

		def __call__(self, sender):
			pc = self.popoverController
			try:
				size = int(sender.get())
			except:
				if self.firstLimit:
					size = tthTool.deltaRange1
				else:
					size = tthTool.deltaRange2
				sender.set(size)

			gm = self.popoverController.gm
			gm.prepareUndo('Change Delta Range')
			if self.firstLimit:
				v1, v2 = size, int(self.cmd.get('ppm2'))
			else:
				v1, v2 = int(self.cmd.get('ppm1')), size
			# if self.cmd.get('code')[0] == 'f':
			# 	tool = tthTool.getTool('Final Delta')
			# else:
			# 	tool = tthTool.getTool('Middle Delta')
			# tool.setRange(v1, v2)
			v1 = str(v1)
			v2 = str(v2)
			self.cmd.set('ppm1', v1)
			self.cmd.set('ppm2', v2)
			pc.popover.DeltaRange1ComboBox.set(v1)
			pc.popover.DeltaRange2ComboBox.set(v2)
			gm.updateGlyphProgram(self.popoverController.fm)
			gm.performUndo()

	def GrayCheckBoxCallback(self, sender):
		if sender.get() == 0:
			self.gm.prepareUndo("Deactivate Delta for Grayscale and Subpixel")
			self.cmd.set('gray', 'false')
		else:
			self.gm.prepareUndo("Activate Delta for Grayscale and Subpixel")
			self.cmd.set('gray', 'true')

		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

	def MonoCheckBoxCallback(self, sender):
		if sender.get() == 0:
			self.gm.prepareUndo("Deactivate Delta for Monochrome")
			self.cmd.set('mono', 'false')
		else:
			self.gm.prepareUndo("Activate Delta for Monochrome")
			self.cmd.set('mono', 'true')

		self.gm.updateGlyphProgram(self.fm)
		self.gm.performUndo()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  I N T E R P O L A T E   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class InterpolatePopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, cmd):
		super(InterpolatePopover, self).__init__(gm, fm, cmd, (200,105), point)

		self.setupStateUI()

		self.setupAlignmentTypeUI(32, withNone = True, show = True)
		alignIdx = gAlignWithNoneTypeToIndex[self.cmd.get('align', 'None')]
		self.popover.alignmentTypePopUpButton.set(alignIdx)

		ll, lw = 65, 80 # labelLeft, labelWidth
		self.setupPointMoverUI(-50, 'point1', 'Move Point 1', ll, lw)
		self.setupPointMoverUI(-35, 'point',  'Move Point',   ll, lw)
		self.setupPointMoverUI(-20, 'point2', 'Move Point 2', ll, lw)

		self.open()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  S I N G L E   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SinglePopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, cmd):
		super(SinglePopover, self).__init__(gm, fm, cmd, (200,130), point)

		self.setupStateUI()
		self.setupRoundDistanceUI()

		stemsX, stemsY = makeStemsLists()
		if self.cmd.get('code')[-1] == 'v':
			self.stemTypeList = stemsY
		else:
			self.stemTypeList = stemsX
		self.stemToIndex = HF.makeListItemToIndexDict(self.stemTypeList)

		self.setupStemTypeUI()

		self.setupAlignmentTypeUI(72, withNone = True, show = True)
		alignIdx = gAlignWithNoneTypeToIndex[self.cmd.get('align', 'None')]
		self.popover.alignmentTypePopUpButton.set(alignIdx)
		noRound = not HF.commandHasAttrib(self.cmd, 'round')
		noStem  = not HF.commandHasAttrib(self.cmd, 'stem')
		self.popover.StemTypePopUpButton.enable(noRound)
		self.popover.alignmentTypePopUpButton.enable(noRound and noStem)

		ll, lw = 65, 80 # labelLeft, labelWidth
		self.setupPointMoverUI(-35, 'point1', 'Move Point 1', ll, lw)
		self.setupPointMoverUI(-20, 'point2', 'Move Point 2', ll, lw)

		self.open()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  D O U B L E   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class DoublePopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, cmd):
		super(DoublePopover, self).__init__(gm, fm, cmd, (200,110), point)

		self.setupStateUI()
		stemsX, stemsY = makeStemsLists()
		if self.cmd.get('code')[-1] == 'v':
			self.stemTypeList = stemsY
		else:
			self.stemTypeList = stemsX
		self.stemToIndex = HF.makeListItemToIndexDict(self.stemTypeList)
		self.setupRoundDistanceUI()
		self.setupStemTypeUI()

		ll, lw = 65, 80 # labelLeft, labelWidth
		self.setupPointMoverUI(-35, 'point1', 'Move Point 1', ll, lw)
		self.setupPointMoverUI(-20, 'point2', 'Move Point 2', ll, lw)

		self.open()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  Z O N E   D E L T A   P O P O V E R
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ZoneDeltaPopover(TTHCommandPopover):
	def __init__(self, gm, fm, point, zoneName, zone):
		super(ZoneDeltaPopover, self).__init__(gm, fm, {}, (200,50), point)
		self.zone = zone
		self.zoneName = zoneName

		self.popover.ZoneDeltaOffsetText = TextBox((10, 10, 100, 15), "Zone Delta Offset:", sizeStyle = "small")
		self.popover.ZoneDeltaOffsetSlider = Slider((10, 25, -10, 15), maxValue=16, value=8, tickMarkCount=17,
				continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.zoneDeltaOffsetSliderCallback)
		self.sizeHasChanged(tthTool.PPM_Size)
		self.open()

	def zoneDeltaOffsetSliderCallback(self, sender):
		zoneDeltaOffset = int(sender.get() - 8)
		self.fm.setZoneDelta((self.zoneName, self.zone), tthTool.PPM_Size, zoneDeltaOffset)
		self.gm.updateGlyphProgram(self.fm)

	def sizeHasChanged(self, size):
		if 'delta' in self.zone:
			ppmStr = str(size)
			if ppmStr in self.zone['delta']:
				self.popover.ZoneDeltaOffsetSlider.set(self.zone['delta'][ppmStr] + 8)
			else:
				self.popover.ZoneDeltaOffsetSlider.set(8)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#  " E X P O R T E D "   F U N C T I O N S
#
#  These are the functions that are supposed to be used from the
#  users of this module
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def openForCommand(cmd, point):
	gm, fm = tthTool.getGlyphAndFontModel()
	code = cmd.get('code')
	if code is None: return
	if code in ['alignh', 'alignv', 'alignt', 'alignb']:
		AlignPopover(gm, fm, point, cmd)
	elif code in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']:
		DeltaPopover(gm, fm, point, cmd)
	elif code in ['singlev', 'singleh']:
		SinglePopover(gm, fm, point, cmd)
	elif code in ['doublev', 'doubleh']:
		DoublePopover(gm, fm, point, cmd)
	elif code in ['interpolatev', 'interpolateh']:
		InterpolatePopover(gm, fm, point, cmd)
	else:
		SimplePopover(gm, fm, point, cmd)
