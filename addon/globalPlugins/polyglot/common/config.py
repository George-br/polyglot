# -*- coding: utf-8 -*-

import config as nvdaConfig
from typing import Any

CONF_SECTION = "modernTranslate"


def getConfig() -> dict[str, Any]:
	"""Provides access to the addon's configuration section."""
	return nvdaConfig.conf[CONF_SECTION]
