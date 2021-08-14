# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Geocoding
Description          : Geocoding and reverse Geocoding using Web Services
Date                 : 25/Jun/2013
copyright            : (C) 2009-2017 by ItOpen
email                : info@itopen.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
__author__ = 'Enrico A. Chiaradia'
__date__ = '2021-08-11'
__copyright__ = '(C) 2021 by Enrico A. Chiaradia'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import qgis
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication,QVariant
from qgis.core import (QgsProcessing,
					   QgsFeatureSink,
					   QgsProcessingAlgorithm,
					   QgsProcessingParameterFeatureSource,
					   QgsProcessingParameterFeatureSink,
					   QgsField,
					   QgsFeature)
						
import os
from ..Utils import pointToWGS84, pointFromWGS84


class BulkReverseGeoCoding(QgsProcessingAlgorithm):
	"""
	This is an example algorithm that takes a vector layer and
	creates a new identical one.

	It is meant to be used as an example of how to create your own
	algorithms and explain methods and variables used to do it. An
	algorithm like this will be available in all elements, and there
	is not need for additional work.

	All Processing algorithms should extend the QgsProcessingAlgorithm
	class.
	"""

	# Constants used to refer to parameters and outputs. They will be
	# used when calling the algorithm from another algorithm, or when
	# calling from the QGIS console.

	SOURCE_LAY = 'SOURCE_LAY'
	OUT_LAY = 'OUT_LAY'

	FEEDBACK = None

	def tr(self, string):
		"""
		Returns a translatable string with the self.tr() function.
		"""
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return BulkReverseGeoCoding()

	def name(self):
		"""
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'BulkReverseGeoCoding'

	def displayName(self):
		"""
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
		return self.tr('Bulk Reverse GeoCoding')

	def group(self):
		"""
		Returns the name of the group this algorithm belongs to. This string
		should be localised.
		"""
		return None

	def groupId(self):
		"""
		Returns the unique ID of the group this algorithm belongs to. This
		string should be fixed for the algorithm, and must not be localised.
		The group id should be unique within each provider. Group id should
		contain lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return None

	def shortHelpString(self):
		"""
		Returns a localised short helper string for the algorithm. This string
		should provide a basic description about what the algorithm does and the
		parameters and outputs associated with it..
		"""
		
		helpStr = """
						Retrieve the address for the selected geometries<sup>1</sup>
						Source layer: where the geometry list is stored [SOURCE_LAY]
						Output layer: the layer that stores results<sup>2</sup> [OUT_LAY]
						<h2>Notes</h2>
						(1) using the geometry centroid
						(2) a new field called 'place' is added to the feature
						"""
		
		return self.tr(helpStr)

	def icon(self):
		self.alg_dir = os.path.dirname(__file__)
		icon = QIcon(os.path.join(self.alg_dir, '../geocode_icon.png'))
		return icon

	def initAlgorithm(self, config=None):
		"""
		Here we define the inputs and output of the algorithm, along
		with some other properties.
		"""
		self.addParameter(QgsProcessingParameterFeatureSource(self.SOURCE_LAY, self.tr('Source table'),
															  [QgsProcessing.TypeVectorAnyGeometry], None, False))

		self.addParameter(QgsProcessingParameterFeatureSink(self.OUT_LAY, self.tr('Output layer'),QgsProcessing.TypeVectorAnyGeometry))

	def processAlgorithm(self, parameters, context, feedback):
		"""
		Here is where the processing itself takes place.
		"""

		self.FEEDBACK = feedback
		# get params
		sourceLay = self.parameterAsSource(parameters, self.SOURCE_LAY, context)

		fldList = sourceLay.fields()
		fieldName = 'place'
		i = 0
		while (fldList.indexFromName(fieldName)>-1):
			fieldName += str(i)
			i+=1

		# add field to store places
		fldList.append(QgsField(fieldName, QVariant.String))

		crs = sourceLay.sourceCrs()
		geomType = sourceLay.wkbType ()

		# make output layer
		(sink, dest_id) = self.parameterAsSink(
			parameters,
			self.OUT_LAY,
			context,
			fldList,
			geomType,
			crs
		)

		# make geocoder machine ...
		geocoder = qgis.utils.plugins['GeoCoding'].get_geocoder_instance()

		c=1
		featureNum = sourceLay.featureCount()

		for feature in sourceLay.getFeatures():
			# get centroid
			centroid = feature.geometry().centroid()
			centroid = pointToWGS84(centroid.asPoint(), crs)

			self.FEEDBACK.pushInfo(self.tr('Searching for centroid: (%s,%s)' % (centroid.x(),centroid.y())))

			# get address
			try:
				result = geocoder.reverse(centroid.x(),centroid.y())
				if len(result)==0:
					self.FEEDBACK.reportError(self.tr('Unable to find the address for the selected geometry'),
											  False)
				else:
					for place, point in result:
						# self.FEEDBACK.pushInfo(self.tr('Point: %s' % (str(point))))
						feat = QgsFeature(fldList)
						feat.setGeometry(feature.geometry())
						feat.setAttributes(feature.attributes()+[place])
						sink.addFeature(feat, QgsFeatureSink.FastInsert)
			except:
				self.FEEDBACK.reportError(self.tr('Unable to add the following feature: %s' % (str(feature))),False)

			self.FEEDBACK.setProgress(100.0 * c / featureNum)
			c+=1

		return {self.OUT_LAY:dest_id}
