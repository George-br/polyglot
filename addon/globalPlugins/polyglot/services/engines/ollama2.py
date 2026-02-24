# -*- coding: utf-8 -*-

import addonHandler

from .ollamaBase import OllamaBaseEngine

addonHandler.initTranslation()


class Ollama2TranslateEngine(OllamaBaseEngine):
	"""
	This is the second instance of the Ollama engine.
	It also inherits all logic and simply overrides the ID and name.
	"""

	id = "ollama2"
	name = _("Ollama 2")
