
from AppKit import NSColor, NSFont, NSFontAttributeName,\
		NSForegroundColorAttributeName, NSBezierPath,\
		NSAttributedString, NSGraphicsContext, NSShadow

from drawing import geom

kArrowColor       = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, .5, 1)
kBlackColor       = NSColor.blackColor()
kBorderColor      = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)
kDeltaColor       = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
kDiscColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
kDoublinkColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, 1, 1)
kFinalDeltaColor  = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)
kInactiveColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, .5, .5, 0.2)
kInterpolateColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.25, .8, 0, 1)
kLinkColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, 0, 1)
kOutlineColor     = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .5)
kRedColor         = NSColor.redColor()
kShadowColor      = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .8)
kSidebearingColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)

kLabelTextAttributes = {
		NSFontAttributeName : NSFont.boldSystemFontOfSize_(9),
		NSForegroundColorAttributeName : NSColor.blackColor(),
		}
kPreviewSizeAttributes = {
		NSFontAttributeName : NSFont.boldSystemFontOfSize_(7),
		NSForegroundColorAttributeName : NSColor.blackColor(),
		}

def drawPreviewSize(title, x, y, color):
	kPreviewSizeAttributes[NSForegroundColorAttributeName] = color
	text = NSAttributedString.alloc().initWithString_attributes_(title, kPreviewSizeAttributes)
	text.drawAtPoint_((x, y))

def drawDiscAtPoint(r, x, y, color):
	color.set()
	NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

def drawCircleAtPoint(r, w, x, y, color):
	color.set()
	path = NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2)))
	path.setLineWidth_(w)
	path.stroke()

def drawSquareAtPoint(d, x, y, color):
	color.set()
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x+d, y+d))
	path.lineToPoint_((x-d, y+d))
	path.lineToPoint_((x-d, y-d))
	path.lineToPoint_((x+d, y-d))
	path.fill()

def drawTriangleAtPoint(d, x, y, color):
	color.set()
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x, y+d))
	path.lineToPoint_((x-d, y-d))
	path.lineToPoint_((x+d, y-d))
	path.fill()

def drawLozengeAtPoint(scale, r, x, y, color):
	color.set()
	d = scale * r
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x+d, y))
	path.lineToPoint_((x, y+d))
	path.lineToPoint_((x-d, y))
	path.lineToPoint_((x, y-d))
	path.lineToPoint_((x+d, y))
	path.fill()

def drawComponentsPoints(scale, glyph, fontModel):
	for c in glyph.components:
		offset_x, offset_y = c.offset
		for c in fontModel.f[c.baseGlyph]:
			for p in c.points:
				pointType = p.type
				if pointType != 'offCurve':
					drawSquareAtPoint(3*scale, p.x + offset_x, p.y + offset_y, kDiscColor)

def drawSideBearingsPointsOfGlyph(scale, size, glyph):
	r = size*scale
	drawDiscAtPoint(r, 0, 0, kDiscColor)
	drawDiscAtPoint(r, glyph.width, 0, kDiscColor)

def drawHorizontalLines(w, yPositions):
	pathY = NSBezierPath.bezierPath()
	for y in yPositions:
		pathY.moveToPoint_((-5000, y))
		pathY.lineToPoint_((+5000, y))
	kSidebearingColor.set()
	pathY.setLineWidth_(w)
	pathY.stroke()

def drawVerticalLines(w, xPositions):
	path = NSBezierPath.bezierPath()
	for x in xPositions:
		path.moveToPoint_((x, -5000))
		path.lineToPoint_((x, +5000))
	kSidebearingColor.set()
	path.setLineWidth_(w)
	path.stroke()

def makeArrowPathAndAnchor(scale, lengthInPixel, direction, tip, path=None):
	dir = lengthInPixel * scale * direction.normalized()
	orth = 0.35 * dir.rotateCCW()
	if path is None:
		pathArrow = NSBezierPath.bezierPath()
	else:
		pathArrow = path
	anchor = tip + dir
	pathArrow.moveToPoint_(tip)
	pathArrow.lineToPoint_(anchor-orth)
	pathArrow.lineToPoint_(anchor+orth)
	pathArrow.lineToPoint_(tip)
	return pathArrow, anchor

def drawArrowAtPoint(scale, r, direction, pos, color):
	path, anchor = makeArrowPathAndAnchor(scale, r, direction, pos)
	color.set()
	path.fill()
	path.setLineWidth_(scale)
	kOutlineColor.set()
	path.stroke()

def drawTextAtPoint(scale, title, pos, textColor, backgroundColor, view, active=True):
	labelColor = backgroundColor
	if not active:
		labelColor = kInactiveColor
		textColor = NSColor.whiteColor()
	else:
		labelColor = backgroundColor

	kLabelTextAttributes[NSForegroundColorAttributeName] = textColor
	text = NSAttributedString.alloc().initWithString_attributes_(title, kLabelTextAttributes)
	width, height = text.size()
	fontSize = kLabelTextAttributes[NSFontAttributeName].pointSize()
	width = width*scale
	width += 8.0*scale
	height = 13*scale

	p = pos - 0.5*geom.Point(width, fontSize*scale)
	unit = geom.Point(scale,scale)
	size = geom.Point(width, height)

	shadow = NSShadow.alloc().init()
	shadow.setShadowColor_(kShadowColor)
	shadow.setShadowOffset_((0, -1))
	shadow.setShadowBlurRadius_(2)

	context = NSGraphicsContext.currentContext()
	#if self.popOverIsOpened and cmdIndex == self.commandClicked and cmdIndex != None:
	#	selectedPath = NSBezierPath.bezierPath()
	#	selectedPath.appendBezierPathWithRoundedRect_xRadius_yRadius_((p-2*unit, size+4*unit), 3*scale, 3*scale)
	#	selectedShadow = NSShadow.alloc().init()
	#	selectedShadow.setShadowColor_(selectedColor)
	#	selectedShadow.setShadowOffset_((0, 0))
	#	selectedShadow.setShadowBlurRadius_(10)
	#	context.saveGraphicsState()
	#	selectedShadow.set()
	#	selectedColor.set()
	#	selectedPath.fill()
	#	context.restoreGraphicsState()

	thePath = NSBezierPath.bezierPath()
	thePath.appendBezierPathWithRoundedRect_xRadius_yRadius_((p, size), 3*scale, 3*scale)

	context.saveGraphicsState()
	shadow.set()
	thePath.setLineWidth_(scale)
	labelColor.set()
	thePath.fill()
	kBorderColor.set()
	thePath.stroke()
	context.restoreGraphicsState()

	view._drawTextAtPoint(title, kLabelTextAttributes, p+0.5*size+geom.Point(0,scale), drawBackground=False)
	return size

def drawSingleArrow(scale, pos1, pos2, color, size=10):
	offCurve = geom.computeOffMiddlePoint(scale, pos1, pos2, size < 0)
	size = abs(size)
	pathArrow, anchor = makeArrowPathAndAnchor(scale, size, offCurve-pos2, pos2)
	path = NSBezierPath.bezierPath()
	path.moveToPoint_(pos1)
	path.curveToPoint_controlPoint1_controlPoint2_(anchor, offCurve, offCurve)
	color.set()
	pathArrow.fill()
	path.setLineWidth_(scale*size/10.0)
	path.stroke()
	return offCurve

def drawDoubleArrow(scale, pos1, pos2, active, iColor, size=10):
	if active:
		color = iColor
	else:
		color = kInactiveColor
	offCurve = geom.computeOffMiddlePoint(scale, pos1, pos2, size < 0)
	size = abs(size)
	pathArrow1, anchor1 = makeArrowPathAndAnchor(scale, size, offCurve-pos1, pos1)
	pathArrow2, anchor2 = makeArrowPathAndAnchor(scale, size, offCurve-pos2, pos2)
	path = NSBezierPath.bezierPath()
	path.moveToPoint_(anchor1)
	path.curveToPoint_controlPoint1_controlPoint2_(anchor2, offCurve, offCurve)
	color.set()
	pathArrow1.fill()
	pathArrow2.fill()
	path.setLineWidth_(scale*size/10.0)
	path.stroke()
	return offCurve

from commons import helperFunctions as HF

class CommandLabel(object):
	def __init__(self, cmd, scale, title, pos, textColor, backgroundColor, active):
		self.cmd = cmd
		self.center = pos
		if not active:
			self.bkgndColor = kInactiveColor
			self.textColor = NSColor.whiteColor()
		else:
			self.bkgndColor = backgroundColor
			self.textColor = textColor

		kLabelTextAttributes[NSForegroundColorAttributeName] = self.textColor
		text = NSAttributedString.alloc().initWithString_attributes_(title, kLabelTextAttributes)
		width, height = text.size()
		self.text = title
		self.fontSize = kLabelTextAttributes[NSFontAttributeName].pointSize()
		width = width*scale
		width += 8.0*scale
		height = 13*scale
		self.size = geom.Point(width, height)
		self.speed = geom.Point(0,0)
		self.count = 0
	
	def reset(self):
		self.speed = geom.Point(0,0);
		self.count = 0
	
	def __lt__(self, other):
		return self.center.y+0.5*self.size.y < other.center.y+0.5*other.size.y

	def lo(self):
		return self.center - 0.5 * self.size

	def hi(self):
		return self.center + 0.5 * self.size
	
	def touch(self, other):
		lo  = self.lo()
		hi  = self.hi()
		olo = other.lo()
		ohi = other.hi()
		xtouch = HF.intervalsIntersect((lo.x, hi.x), (olo.x, ohi.x))
		ytouch = HF.intervalsIntersect((lo.y, hi.y), (olo.y, ohi.y))
		return xtouch and ytouch

	def updateSpeed(self, other):
		diff = self.center - other.center
		if diff.length() < 0.1:
			weird = True
			diff = geom.Point(0,1)
		minDiffX = 1.0*(0.51 * (self.size.x + other.size.x) - abs(diff.x))
		minDiffY = 1.0*(0.51 * (self.size.y + other.size.y) - abs(diff.y))
		workInX = 0
		#diff = diff.normalized()
		if minDiffX > 0.0 and abs(diff.x) > 0.000001:
			workInX = minDiffX/abs(diff.x)
		workInY = 0
		if minDiffY > 0.0 and abs(diff.y) > 0.000001:
			workInY = minDiffY/abs(diff.y)
		if workInX == 0 and workInY == 0: return
		if workInX == 0:
			work = 0.5 * workInY
		elif workInY == 0:
			work = 0.5 * workInX
		else:
			work = 0.5 * min(workInX, workInY)
		self.speed = self.speed + work * diff
		other.speed = other.speed - work * diff
		self.count += 1
		other.count += 1

	def draw(self, scale, nsView):
		shadow = NSShadow.alloc().init()
		shadow.setShadowColor_(kShadowColor)
		shadow.setShadowOffset_((0, -1))
		shadow.setShadowBlurRadius_(2)

		corner = self.center - 0.5*geom.Point(self.size.x, self.fontSize*scale)

		context = NSGraphicsContext.currentContext()

		thePath = NSBezierPath.bezierPath()
		thePath.appendBezierPathWithRoundedRect_xRadius_yRadius_((corner, self.size), 3*scale, 3*scale)

		context.saveGraphicsState()
		shadow.set()
		thePath.setLineWidth_(scale)
		self.bkgndColor.set()
		thePath.fill()
		kBorderColor.set()
		thePath.stroke()
		context.restoreGraphicsState()
		kLabelTextAttributes[NSForegroundColorAttributeName] = self.textColor
		nsView._drawTextAtPoint(self.text, kLabelTextAttributes, corner+0.5*self.size+geom.Point(0,scale), drawBackground=False)

from bisect import insort

def untangleLabels(labels):
	someContact = False
	for cl in labels:
		cl.reset()
	below = []
	labels.sort(key=lambda l:l.center.y-0.5*l.size.y)
	for cl in labels:
		below_bottom = cl.lo()
		while below and below[0].hi().y < below_bottom.y:
			below.pop()
		for candidate in below:
			if cl.touch(candidate):
				someContact = True
				cl.updateSpeed(candidate)
		insort(below, cl)
	if not someContact:
		return False
	for cl in labels:
		if cl.count == 0: continue
		cl.center = cl.center + (1.0 / cl.count) * cl.speed
	return True
