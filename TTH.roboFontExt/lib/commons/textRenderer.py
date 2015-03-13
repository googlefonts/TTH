from objc import allocateBuffer
from AppKit import *
import Quartz
from mojo.UI import *
try:
	import freetype as FT
except:
	print 'ERROR: freetype not installed'

grayCS = Quartz.CGColorSpaceCreateDeviceGray()
rgbCS = Quartz.CGColorSpaceCreateDeviceRGB()

class TRCache (object):
	def __init__(self):
		self.images = {}
		self.contours_points_and_tags = {}
		self.bezier_paths = {}
		self.bitmaps = {}
		self.advances = {}


class TextRenderer(object):
	def __init__(self, face_path, renderMode):
		try:
			self.face = FT.Face(face_path)
			# the glyph slot in the face, from which we extract the images
			# (contour) of requested glyphs, before storing them in the
			# cache
			self.slot = self.face.glyph
		except:
			self.face = None
			print 'ERROR: FreeType could not load temporary font'
		# a dictionary mapping text size in pixel to the TRCache
		# storing the glyphs images/bitmaps/advances already loaded.
		self.caches = {} 
		# The TRCache for the current text pixel-size
		self.cache = None
		# current text pixel-size
		self.curSize = 0
		# drawing position
		self.pen = (0,0)
		self.set_cur_size(9)

		self.outlinecolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)

		self.render_func = drawBitmapGray
		self.render_mode = FT.FT_RENDER_MODE_NORMAL
		if renderMode == 'Monochrome':
			self.render_mode = FT.FT_RENDER_MODE_MONO
			self.render_func = drawBitmapMono
		elif renderMode == 'Subpixel':
			self.render_mode = FT.FT_RENDER_MODE_LCD
			self.render_func = drawBitmapSubPixelColor

		self.load_mode = FT.FT_LOAD_DEFAULT
		#self.load_mode = FT.FT_LOAD_RENDER
		if renderMode == 'Monochrome':
			self.load_mode = self.load_mode | FT.FT_LOAD_TARGET_MONO
		elif renderMode == 'Subpixel':
			self.load_mode = self.load_mode | FT.FT_LOAD_TARGET_LCD
		else:
			self.load_mode = self.load_mode | FT.FT_LOAD_TARGET_NORMAL

	def set_pen(self, p):
		self.pen = p

	def get_pen(self):
		return self.pen

	def set_cur_size(self, size):
		if size < 4:
			self.curSize = 4
		else:
			self.curSize = int(size)
		# select the TRCache of proper size
		if self.curSize not in self.caches:
			self.caches[self.curSize] = TRCache()
		self.cache = self.caches[self.curSize]

	def render_text_with_scale_and_alpha(self, text, scale, alpha):
		if self.face == None:
			return
		org = self.pen
		for c in text:
			index = self.face.get_char_index(c)
			self.render_func(self.get_glyph_bitmap(index), scale, self.pen[0], self.pen[1], alpha)
			self.pen = (self.pen[0] + int( self.get_advance(index)[0] / 64 ), self.pen[1])
		return (self.pen[0] - org[0], self.pen[1] - org[1])

	def render_text(self, text):
		return self.render_text_with_scale_and_alpha(text, 1, 1.0)

	def render_indexed_glyph_list(self, idxes, scale=1, alpha=1.0):
		if self.face == None:
			return
		org = self.pen
		try:
			for index in idxes:
				self.render_func(self.get_glyph_bitmap(index), scale, self.pen[0], self.pen[1], alpha)
				self.pen = (self.pen[0] + int( self.get_advance(index)[0] / 64 ), self.pen[1])
		except:
			pass
		return (self.pen[0] - org[0], self.pen[1] - org[1])

	def names_to_indices(self, names):
		return [self.face.get_name_index(name) for name in names]

	def render_named_glyph_list(self, nameList, scale=1, alpha=1.0):
		indices = self.names_to_indices(nameList)
		return self.render_indexed_glyph_list(indices, scale, alpha)

	def get_advance(self, index):
		return self.cache.advances[index]

	def get_char_advance(self, char):
		return self.get_advance(self.face.get_char_index(char))

	def get_name_advance(self, name):
		return self.get_advance(self.face.get_name_index(name))

	def get_glyph_contours_points_and_tags(self, index):
		if index not in self.cache.contours_points_and_tags:
			self.get_glyph_image(index)
		return self.cache.contours_points_and_tags[index]

	def get_char_contours_points_and_tags(self, char):
		return self.get_glyph_contours_points_and_tags(self.face.get_char_index(char))

	def get_glyph_image(self, index):
		# a glyph image (contours) is requested. If not in the cache,
		# we load it with freetype and save it in the cache and return
		# it
		if index not in self.cache.images:
			self.face.set_pixel_sizes(0, int(self.curSize))
			self.face.load_glyph(index, self.load_mode)

			result = self.slot.get_glyph() # this returns a copy
			self.cache.images[index] = result
			self.cache.advances[index] = (self.slot.advance.x, self.slot.advance.y)
			pts = list(self.slot.outline.points) # copy
			cts = list(self.slot.outline.contours) # copy
			tgs = list(self.slot.outline.tags) # copy
			self.cache.contours_points_and_tags[index] = (cts, pts, tgs)
			return result
		else:
			return self.cache.images[index]

	def get_char_image(self, char):
		# convert unicode-char to glyph-index and then call get_glyph_image
		return self.get_glyph_image(self.face.get_char_index(char))

	def get_glyph_bitmap(self, index):
		# a glyph bitmap (pixel buffer) is requested. If not in the cache,
		# we render it with freetype and save it in the cache and return
		# it
		if index not in self.cache.bitmaps:
			#print "!! ", self.get_glyph_image(index).format,
			result = self.get_glyph_image(index).to_bitmap(self.render_mode, 0)
			if self.render_mode == FT.FT_RENDER_MODE_LCD:
				result = (result, desaturateBufferFromFTBuffer(result))
			#print self.get_glyph_image(index).format
			self.cache.bitmaps[index] = result
			return result
		else:
			return self.cache.bitmaps[index]

	def get_char_bitmap(self, char):
		# convert unicode-char to glyph-index and then call get_glyph_bitmap
		return self.get_glyph_bitmap(self.face.get_char_index(char))

	def drawOutline(self, scale, paths, thickness):
		if paths is None:
			return
		self.outlinecolor.set()
		for p  in paths:
			p.setLineWidth_(scale*thickness)
			p.stroke()

	def drawOutlineOfChar(self, scale, pitch, char):
		self.drawOutline(scale, self.getBezierPathOfChar(scale, pitch, char))

	def drawOutlineOfNameWithThickness(self, scale, pitch, name, thickness):
		self.drawOutline(scale, self.getBezierPathOfName(scale, pitch, name), thickness)

	def getBezierPathOfName(self, scale, pitch, name):
		index = self.face.get_name_index(name)
		return self.getBezierPath(scale, pitch, index)

	def getBezierPathOfChar(self, scale, pitch, char):
		index = self.face.get_char_index(char)
		return self.getBezierPath(scale, pitch, index)

	def getBezierPath(self, scale, pitch, index):
		try:
			return self.cache.bezier_paths[index]
		except:
			pass
		#print outline.contours

		(contours, points, itags) = self.get_glyph_contours_points_and_tags(index)
		if len(contours) == 0:
			return None
		adaptedOutline_points = [(int(pitch*p[0]/64), int(pitch*p[1]/64)) for p in points]
		paths = []
		pathContour = NSBezierPath.bezierPath()
		start = 0
		for end in contours:
			points	= adaptedOutline_points[start:end+1]
			points.append(points[0])
			tags	= itags[start:end+1]
			tags.append(tags[0])

			segments = [ [points[0],], ]

			for j in range(1, len(points) ):
				segments[-1].append(points[j])
				if tags[j] & (1 << 0) and j < (len(points)-1):
					segments.append( [points[j],] )
			pathContour.moveToPoint_((points[0][0], points[0][1]))
			for segment in segments:
				if len(segment) == 2:
					pathContour.lineToPoint_(segment[1])
				else:
					onCurve = segment[0]
					for i in range(1,len(segment)-2):
						A,B = segment[i], segment[i+1]
						nextOn = ((A[0]+B[0])/2.0, (A[1]+B[1])/2.0)
						antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
						antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
						pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)
						onCurve = nextOn
					nextOn = segment[-1]
					A = segment[-2]
					antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
					antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
					pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)
			start = end+1
			paths.append(pathContour)
		self.cache.bezier_paths[index] = paths
		return paths


# DRAWING FUNCTIONS


def drawBitmapMono(bmg, scale, advance, height, alpha):
	# 'bmg' stands for BitMapGlyph, a data structure from freetype.
	bm = bmg.bitmap
	numBytes = bm.rows * bm.pitch
	if numBytes == 0:
		return
	buf = allocateBuffer(numBytes)
	ftBuffer = bm._FT_Bitmap.buffer
	for i in range(numBytes):
		buf[i] = ftBuffer[i]

	#provider = Quartz.CGDataProviderCreateWithData(None, bm._FT_Bitmap.buffer, numBytes, None)
	provider = Quartz.CGDataProviderCreateWithData(None, buf, numBytes, None)

	cgimg = Quartz.CGImageCreate(
			bm.width,
			bm.rows,
			1, # bit per component
			1, # size_t bitsPerPixel,
			bm.pitch, # size_t bytesPerRow,
			grayCS, # CGColorSpaceRef colorspace,
			Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
	destRect = Quartz.CGRectMake(bmg.left*scale + advance, (bmg.top-bm.rows)*scale + height, bm.width*scale, bm.rows*scale)
	
	port = NSGraphicsContext.currentContext().graphicsPort()
	if alpha < 1:
		Quartz.CGContextSetAlpha(port, alpha)
	Quartz.CGContextSetBlendMode(port, Quartz.kCGBlendModeDifference)
	Quartz.CGContextSetInterpolationQuality(port, Quartz.kCGInterpolationNone)
	Quartz.CGContextDrawImage(port, destRect, cgimg)
	if alpha < 1:
		Quartz.CGContextSetAlpha(port, 1)
	Quartz.CGContextSetBlendMode(port, Quartz.kCGBlendModeNormal)

def drawBitmapGray(bmg, scale, advance, height, alpha):
	bm = bmg.bitmap
	numBytes = bm.rows * bm.pitch
	if numBytes == 0:
		return
	buf = allocateBuffer(numBytes)
	ftBuffer = bm._FT_Bitmap.buffer
	for i in range(numBytes):
		buf[i] = ftBuffer[i]

	provider = Quartz.CGDataProviderCreateWithData(None, buf, numBytes, None)

	cgimg = Quartz.CGImageCreate(
			bm.width,
			bm.rows,
			8, # bit per component
			8, # size_t bitsPerPixel,
			bm.pitch, # size_t bytesPerRow,
			grayCS, # CGColorSpaceRef colorspace,
			Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
	destRect = Quartz.CGRectMake(bmg.left*scale + advance, (bmg.top-bm.rows)*scale + height, bm.width*scale, bm.rows*scale)
	
	port = NSGraphicsContext.currentContext().graphicsPort()
	if alpha < 1.0:
		Quartz.CGContextSetAlpha(port, alpha)
	Quartz.CGContextSetBlendMode(port, Quartz.kCGBlendModeDifference)
	Quartz.CGContextSetInterpolationQuality(port, Quartz.kCGInterpolationNone)
	Quartz.CGContextDrawImage(port, destRect, cgimg)
	if alpha < 1.0:
		Quartz.CGContextSetAlpha(port, 1.0)
	Quartz.CGContextSetBlendMode(port, Quartz.kCGBlendModeNormal)

def desaturateBufferFromFTBuffer(bmg):
	bm = bmg.bitmap
	pixelWidth = int(bm.width/3)
	numBytes = 4 * bm.rows * pixelWidth
	if numBytes == 0:
		return
	buf = allocateBuffer(numBytes)
	ftBuffer = bm._FT_Bitmap.buffer
	pos = 0
	for i in range(bm.rows):
		source = bm.pitch * i
		for j in range(pixelWidth):
			ftSub = ftBuffer[source:source+3];
			gray = (1.0 - 0.4) * sum([x*y for x,y in zip([0.3086, 0.6094, 0.0820], ftSub)])
			buf[pos:pos+3] = [int(0.4 * x + gray) for x in ftSub]
			buf[pos+3] = 0
			pos += 4
			source += 3
	provider = Quartz.CGDataProviderCreateWithData(None, buf, numBytes, None)
	cgimg = Quartz.CGImageCreate(
			pixelWidth,
			bm.rows,
			8, # bit per component
			32, # size_t bitsPerPixel,
			4 * pixelWidth, # size_t bytesPerRow,
			rgbCS, # CGColorSpaceRef colorspace,
			Quartz.kCGImageAlphaNone, # CGBitmapInfo bitmapInfo,
			#Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
	return cgimg

def drawBitmapSubPixelColor((bmg, cgimg), scale, advance, height, alpha):
	bm = bmg.bitmap
	pixelWidth = int(bm.width/3)
	destRect = Quartz.CGRectMake(bmg.left*scale + advance, (bmg.top-bm.rows)*scale + height, pixelWidth*scale, bm.rows*scale)
	port = NSGraphicsContext.currentContext().graphicsPort()
	if alpha < 1:
		Quartz.CGContextSetAlpha(port, alpha)
	Quartz.CGContextSetBlendMode(port, Quartz.kCGBlendModeDifference)
	Quartz.CGContextSetInterpolationQuality(port, Quartz.kCGInterpolationNone)
	Quartz.CGContextDrawImage(port, destRect, cgimg )
	Quartz.CGContextSetBlendMode(port, Quartz.kCGBlendModeNormal)
	if alpha < 1:
		Quartz.CGContextSetAlpha(port, 1)
