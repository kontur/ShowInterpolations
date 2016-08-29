# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################


from GlyphsApp.plugins import *
import math

class ShowInterpolation(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Interpolations',
			'de': u'Interpolationen',
			'es': u'interpolaciones',
			'fr': u'interpolations'
		})
		
		# default centering setting:
		if Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] is None:
			Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] = False
	
	def transform(self, shiftX=0.0, shiftY=0.0, rotate=0.0, skew=0.0, scale=1.0):
		"""
		Returns an NSAffineTransform object for transforming layers.
		Apply an NSAffineTransform t object like this:
			Layer.transform_checkForSelection_doComponents_(t,False,True)
		Access its transformation matrix like this:
			tMatrix = t.transformStruct() # returns the 6-float tuple
		Apply the matrix tuple like this:
			Layer.applyTransform(tMatrix)
			Component.applyTransform(tMatrix)
			Path.applyTransform(tMatrix)
		Chain multiple NSAffineTransform objects t1, t2 like this:
			t1.appendTransform_(t2)
		"""
		myTransform = NSAffineTransform.transform()
		if rotate:
			myTransform.rotateByDegrees_(rotate)
		if scale != 1.0:
			myTransform.scaleBy_(scale)
		if not (shiftX == 0.0 and shiftY == 0.0):
			myTransform.translateXBy_yBy_(shiftX,shiftY)
		if skew:
			skewStruct = NSAffineTransformStruct()
			skewStruct.m11 = 1.0
			skewStruct.m22 = 1.0
			skewStruct.m21 = math.tan(math.radians(skew))
			skewTransform = NSAffineTransform.transform()
			skewTransform.setTransformStruct_(skewStruct)
			myTransform.appendTransform_(skewTransform)
		return myTransform
	
	def recenterLayer(self, Layer, newCenterX):
		centerX = Layer.bounds.origin.x + Layer.bounds.size.width/2
		if centerX != newCenterX:
			shift = self.transform( float(newCenterX-centerX) )
			Layer.transform_checkForSelection_doComponents_(shift,False,False)
		return Layer
	
	def background(self, Layer):
		Glyph = Layer.parent
		Font = Glyph.parent
		Instances = [ i for i in Font.instances if i.active ]
		shouldCenter = Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]
		centerX = Layer.bounds.origin.x + Layer.bounds.size.width/2
	
		if len( Instances ) > 0:
			# display all instances that have a custom parameter:
			displayedInterpolationCount = 0
			for thisInstance in Instances:
				showInterpolationValue = thisInstance.customParameters["ShowInterpolation"]
				if showInterpolationValue is not None:
					interpolatedLayer = self.glyphInterpolation( Glyph, thisInstance )
					if shouldCenter:
						interpolatedLayer = self.recenterLayer(interpolatedLayer, centerX)
					displayedInterpolationCount += 1
					if interpolatedLayer is not None:
						self.colorForParameterValue( showInterpolationValue ).set()
						self.bezierPathComp(interpolatedLayer).fill()
			
			# if no custom parameter is set, display them all:
			if displayedInterpolationCount == 0:
				self.colorForParameterValue( None ).set()
				for thisInstance in Instances:
					interpolatedLayer = self.glyphInterpolation( Glyph, thisInstance )
					if shouldCenter:
						interpolatedLayer = self.recenterLayer(interpolatedLayer, centerX)
					if interpolatedLayer is not None:
						self.bezierPathComp(interpolatedLayer).fill()

	def bezierPathComp( self, thisPath ):
		"""Compatibility method for bezierPath before v2.3."""
		try:
			return thisPath.bezierPath() # until v2.2
		except Exception as e:
			return thisPath.bezierPath # v2.3+
	
	def glyphInterpolation( self, thisGlyph, thisInstance ):
		"""
		Yields a layer.
		"""
		try:
			interpolatedFont = thisInstance.pyobjc_instanceMethods.interpolatedFont()
			interGlyphs = interpolatedFont.glyphForName_(thisGlyph.name)
			interpolatedLayer = interGlyphs.layerForKey_(interpolatedFont.fontMasterID())
			thisFont = thisGlyph.parent
			if not thisInstance.customParameters["Grid Spacing"] and not ( thisFont.gridMain() / thisFont.gridSubDivision() ):
				interpolatedLayer.roundCoordinates()
			if len( interpolatedLayer.paths ) != 0:
				return interpolatedLayer
			else:
				return None
		except:
			import traceback
			print traceback.format_exc()
			return None
	
	def colorForParameterValue( self, parameterString ):
		"""
		Turns '0.3;0.4;0.9' into RGB values and returns an NSColor object.
		"""
		try:
			# default color:
			RGBA = [ 0.4, 0.0, 0.3, 0.15 ]
			
			# if set, take user input as color:
			if parameterString is not None:
				parameterValues = parameterString.split(";")
				for i in range(len( parameterValues )):
					thisValueString = parameterValues[i]
					try:
						thisValue = abs(float( thisValueString ))
						if thisValue > 1.0:
							thisValue %= 1.0
						RGBA[i] = thisValue
					except Exception as e:
						pass
						# self.logToConsole( "Could not convert '%s' (from '%s') to a float. Keeping default." % (thisValueString, parameterString) )
			
			# return the color:
			thisColor = NSColor.colorWithCalibratedRed_green_blue_alpha_( RGBA[0], RGBA[1], RGBA[2], RGBA[3] )
			return thisColor
		except Exception as e:
			self.logToConsole( "colorForParameterValue: %s" % str(e) )
	
	def conditionalContextMenus(self):
		# Empty list of context menu items
		contextMenus = []
		if not Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]:
			contextMenus.append(
				{
					'name': Glyphs.localize({
						'en': u'Center Interpolations',
						'de': u'Interpolationen zentrieren',
						'es': u'Centrar las interpolaciones',
						'fr': u'Centrer les interpolations'
					}), 'action': self.toggleCentering
				},
			)
		else:
			contextMenus.append(
				{
					'name': Glyphs.localize({
						'en': u'Do Not Center Interpolations',
						'de': u'Interpolationen nicht zentrieren',
						'es': u'No centrar las interpolaciones',
						'fr': u'Ne pas centrer les interpolations'
					}), 'action': self.toggleCentering
				},
			)

		# Return list of context menu items
		return contextMenus

	def toggleCentering(self):
		Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] = not Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]
		Glyphs.update()
		