# -*- coding: utf-8 -*-

import importlib
import inspect
import pkgutil

from logHandler import log

from . import engines
from .engine import TranslationEngine

_engineInstances: list[TranslationEngine] | None = None


def _scanAndLoadEngines() -> None:
	global _engineInstances
	log.debug("First-time scan: Loading translation engines...")
	_engineInstances = []
	for _, name, _ in pkgutil.iter_modules(engines.__path__, engines.__name__ + "."):
		try:
			module = importlib.import_module(name)
			for _, memberObj in inspect.getmembers(module):
				if (
					inspect.isclass(memberObj)
					and issubclass(memberObj, TranslationEngine)
					and memberObj is not TranslationEngine
					and not inspect.isabstract(memberObj)
				):
					instance: TranslationEngine = memberObj()
					_engineInstances.append(instance)
					log.debug(f"Successfully loaded engine: {instance.name} (ID: {instance.id})")
		except Exception:
			log.error(f"Failed to load engine module '{name}'", exc_info=True)
	if not _engineInstances:
		log.warning(
			"""No translation engines were loaded successfully. This may be due to errors in the engine modules or an issue with the add-on installation. Translation functionality will not be available."""
		)
	assert _engineInstances is not None
	_engineInstances.sort(key=lambda e: e.name)


def getAllEngines() -> list[TranslationEngine]:
	global _engineInstances
	if _engineInstances is None:
		_scanAndLoadEngines()
	assert _engineInstances is not None
	return _engineInstances


def getEngineById(engineId: str) -> TranslationEngine:
	allEngines = getAllEngines()
	for engine in allEngines:
		if engine.id == engineId:
			return engine
	raise ValueError(f"Engine with ID '{engineId}' not found.")
