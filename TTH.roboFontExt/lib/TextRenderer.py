
from objc import allocateBuffer
import Quartz
from mojo.UI import *
import freetype as FT


class TRCache (object):
	def __init__(self):
		self.images = {}
		self.bitmaps = {}
		self.advances = {}

class TextRenderer (object):

	def __init__(self, face_path, renderMode):
		self.face = FT.Face(face_path)
		self.glyph = self.face.glyph
		self.caches = {}
		self.cache = None
		self.curSize = 0
		self.pen = (0,0)
		self.set_cur_size(9)

		self.render_func = drawBitmapGray
		self.render_mode = FT.FT_RENDER_MODE_NORMAL
		if renderMode == 'Monochrome':
			self.render_mode = FT.FT_RENDER_MODE_MONO
			self.render_func = drawBitmapMono
		elif renderMode == 'Subpixel':
			self.render_mode = FT.FT_RENDER_MODE_LCD
			self.render_func = drawBitmapSubPixelColor

	def set_pen(self, p):
		self.pen = p

	def set_cur_size(self, size):
		if size < 4:
			self.curSize = 4
		else:
			self.curSize = int(size)
		if self.curSize not in self.caches:
			self.caches[self.curSize] = TRCache()
		self.cache = self.caches[self.curSize]

	def render_text_with_scale_and_alpha(self, text, scale, alpha):
		org = self.pen
		for c in text:
			index = self.face.get_char_index(c)
			self.render_func(self.get_glyph_bitmap(index), scale, self.pen[0], self.pen[1], alpha)
			self.pen = (self.pen[0] + int( self.get_advance(index)[0] / 64 ), self.pen[1])
		return (self.pen[0] - org[0], self.pen[1] - org[1])

	def render_text(self, text):
		return self.render_text_with_scale_and_alpha(text, 1, 1.0)

	def get_advance(self, index):
		return self.cache.advances[index]

	def get_glyph_image(self, index):
		if index not in self.cache.images:
			self.face.set_pixel_sizes(0, int(self.curSize))
			self.face.load_glyph(index, FT.FT_LOAD_DEFAULT)
			temp = self.glyph.get_glyph()
			self.cache.images[index] = temp
			self.cache.advances[index] = (self.glyph.advance.x, self.glyph.advance.y)
			return temp
		else:
			return self.cache.images[index]

	def get_char_image(self, char):
		return self.get_glyph_image(self.face.get_char_index(char))

	def get_glyph_bitmap(self, index):
		if index not in self.cache.bitmaps:
			temp = self.get_glyph_image(index).to_bitmap(self.render_mode, 0)
			self.cache.bitmaps[index] = temp
			return temp
		else:
			return self.cache.bitmaps[index]

	def get_char_bitmap(self, char):
		return self.get_glyph_bitmap(self.face.get_char_index(char))

def drawBitmapMono(bmg, scale, advance, height, alpha):
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

	colorspace = Quartz.CGColorSpaceCreateDeviceGray()
	cgimg = Quartz.CGImageCreate(
			bm.width,
			bm.rows,
			1, # bit per component
			1, # size_t bitsPerPixel,
			bm.pitch, # size_t bytesPerRow,
			colorspace, # CGColorSpaceRef colorspace,
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

	colorspace = Quartz.CGColorSpaceCreateDeviceGray()
	cgimg = Quartz.CGImageCreate(
			bm.width,
			bm.rows,
			8, # bit per component
			8, # size_t bitsPerPixel,
			bm.pitch, # size_t bytesPerRow,
			colorspace, # CGColorSpaceRef colorspace,
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

def drawBitmapSubPixelColor(bmg, scale, advance, height, alpha):
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

	colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
	cgimg = Quartz.CGImageCreate(
			pixelWidth,
			bm.rows,
			8, # bit per component
			32, # size_t bitsPerPixel,
			4 * pixelWidth, # size_t bytesPerRow,
			colorspace, # CGColorSpaceRef colorspace,
			Quartz.kCGImageAlphaNone, # CGBitmapInfo bitmapInfo,
			#Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
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
