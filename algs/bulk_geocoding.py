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
					   QgsProcessingParameterField,
					   QgsWkbTypes,
					   QgsField,
					   QgsProject,
					   QgsFeature,
					   QgsGeometry,
					   QgsPointXY)

import os

from ..Utils import pointToWGS84, pointFromWGS84


class BulkGeoCoding(QgsProcessingAlgorithm):
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

	SOURCE_TABLE = 'SOURCE_TABLE'
	ADDRESS_FLD = 'ADDRESS_FLD'
	OUT_LAY = 'OUT_LAY'

	FEEDBACK = None

	def tr(self, string):
		"""
		Returns a translatable string with the self.tr() function.
		"""
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return BulkGeoCoding()

	def name(self):
		"""
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'BulkGeoCoding'

	def displayName(self):
		"""
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
		return self.tr('Bulk GeoCoding')

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
						Retrieve coodinates<sup>1</sup> from a list of addresses
						Source table: where the address list is stored [SOURCE_TABLE]
						Address: the field that contains the address to search/geocode [ADDRESS_FLD]
						Output layer: the layer that stores results<sup>2</sup> [OUT_LAY]
						<h2>Notes</h2>
						(1) using the service defined in the plugin settings
						(2) a new field called 'place' is added to store search results
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
		self.addParameter(QgsProcessingParameterFeatureSource(self.SOURCE_TABLE, self.tr('Source table'),
															  [QgsProcessing.TypeFile], None, False))

		self.addParameter(QgsProcessingParameterField(self.ADDRESS_FLD, self.tr('Address'), 'address', self.SOURCE_TABLE,
													  QgsProcessingParameterField.String))

		self.addParameter(QgsProcessingParameterFeatureSink(self.OUT_LAY, self.tr('Output layer'),QgsProcessing.TypeVectorPoint))

	def processAlgorithm(self, parameters, context, feedback):
		"""
		Here is where the processing itself takes place.
		"""

		self.FEEDBACK = feedback
		# get params
		sourceTable = self.parameterAsSource(parameters, self.SOURCE_TABLE, context)
		addressFld = self.parameterAsFields(parameters, self.ADDRESS_FLD, context)
		addressFld = addressFld[0]

		fldList = sourceTable.fields()
		# add field to store places
		fieldName = 'place'
		i = 0
		while (fldList.indexFromName(fieldName) > -1):
			fieldName += str(i)
			i += 1

		fldList.append(QgsField(fieldName, QVariant.String))

		#crs = QgsCoordinateReferenceSystem('4326')
		crs = QgsProject.instance().crs()

		# make output layer
		(sink, dest_id) = self.parameterAsSink(
			parameters,
			self.OUT_LAY,
			context,
			fldList,
			QgsWkbTypes.Point,
			crs
		)

		# make geocoder machine ...
		geocoder = qgis.utils.plugins['GeoCoding'].get_geocoder_instance()

		c=1
		featureNum = sourceTable.featureCount()

		for feature in sourceTable.getFeatures():
			# get address
			point = None
			newPoint = None
			place = None
			address = feature[addressFld]
			self.FEEDBACK.pushInfo(self.tr('Processing the following address: %s' % (str(address))))
			try:
				result = geocoder.geocode(unicode(address).encode('utf-8'))
				if len(result)==0:
					self.FEEDBACK.reportError(self.tr('Unable to find the selected address'),
											  False)
				else:
					for place, point in result:
						# self.FEEDBACK.pushInfo(self.tr('Point: %s' % (str(point))))
						feat = QgsFeature(fldList)
						newPoint = pointFromWGS84(QgsPointXY(float(point[0]), float(point[1])), crs)
						feat.setGeometry(QgsGeometry().fromPointXY(newPoint))
						feat.setAttributes(feature.attributes()+[place])
						sink.addFeature(feat, QgsFeatureSink.FastInsert)
			except:
				self.FEEDBACK.reportError(self.tr('Unable to add the following address: %s' % (str(address))),False)
				self.FEEDBACK.reportError(self.tr('Point: %s' % (str(point))),False)
				self.FEEDBACK.reportError(self.tr('Place: %s' % (str(place))),False)

			self.FEEDBACK.setProgress(100.0 * c / featureNum)
			c+=1

		return {self.OUT_LAY:dest_id}
