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
__date__ = '2020-12-01'
__copyright__ = '(C) 2020 by Enrico A. Chiaradia'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.core import QgsProcessingProvider

from PyQt5.QtGui import QIcon

from .algs.bulk_reverse_geocoding import BulkReverseGeoCoding
from .algs.bulk_geocoding import BulkGeoCoding


class GeoCodingProvider(QgsProcessingProvider):

	def __init__(self):
		QgsProcessingProvider.__init__(self)

		# Load algorithms
		self.alglist = [BulkGeoCoding(),
						BulkReverseGeoCoding()
						]

	def unload(self):
		"""
		Unloads the provider. Any tear-down steps required by the provider
		should be implemented here.
		"""
		pass

	def loadAlgorithms(self):
		"""
		Loads all algorithms belonging to this provider.
		"""
		for alg in self.alglist:
			self.addAlgorithm( alg )

	def id(self):
		"""
		Returns the unique provider id, used for identifying the provider. This
		string should be a unique, short, character only string, eg "qgis" or
		"gdal". This string should not be localised.
		"""
		return 'geocodings'

	def name(self):
		"""
		Returns the provider name, which is used to describe the provider
		within the GUI.

		This string should be short (e.g. "Lastools") and localised.
		"""
		return self.tr('Geocoding')

	def longName(self):
		"""
		Returns the a longer version of the provider name, which can include
		extra details such as version numbers. E.g. "Lastools LIDAR tools
		(version 2.2.1)". This string should be localised. The default
		implementation returns the same string as name().
		"""
		return self.tr('Geocoding')

	def icon(self):
		self.plugin_dir = os.path.dirname(__file__)
		icon = QIcon(os.path.join(self.plugin_dir, 'geocode_icon.png'))
		return icon