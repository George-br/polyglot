# -*- coding: utf-8 -*-

import hashlib
import json
import os
from typing import Any, Self  # Self is available in Python 3.11+

import globalVars
from logHandler import log


class TranslationCache:
	"""Provides a simple, persistent cache for translation results. Implemented as a singleton."""

	_instance: Self | None = None

	cachePath: str
	maxSize: int
	_cache: dict[str, str]
	_initialized: bool

	def __new__(cls, *args: Any, **kwargs: Any) -> Self:
		if not cls._instance:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self, filename: str = "translation_cache.json", maxSize: int = 10000) -> None:
		super().__init__()
		if hasattr(self, "_initialized"):
			return
		configPath = globalVars.appArgs.configPath
		self.cachePath = os.path.join(configPath, filename)
		self.maxSize = maxSize
		self._cache = self._load()
		self._initialized = True
		log.info(f"TranslationCache initialized. Path: {self.cachePath}, Initial items: {len(self._cache)}")

	def _load(self) -> dict[str, str]:
		try:
			if os.path.exists(self.cachePath):
				with open(self.cachePath, "r", encoding="utf-8") as f:
					loadedData = json.load(f)
					if isinstance(loadedData, dict):
						return loadedData
		except (IOError, json.JSONDecodeError):
			log.error(f"Failed to load translation cache from {self.cachePath}", exc_info=True)
			pass
		return {}

	def _save(self) -> None:
		try:
			if len(self._cache) > self.maxSize:
				keysToDelete = list(self._cache.keys())[: len(self._cache) - self.maxSize]
				for key in keysToDelete:
					del self._cache[key]
				log.info(f"Cache size exceeded {self.maxSize}. Pruned {len(keysToDelete)} items.")
			with open(self.cachePath, "w", encoding="utf-8") as f:
				json.dump(self._cache, f, ensure_ascii=False, indent=2)
		except IOError:
			log.error(f"Failed to save translation cache to {self.cachePath}", exc_info=True)
			pass

	def buildKey(self, langFrom: str, langTo: str, text: str) -> str:
		"""Generates a unique cache key by hashing the language pair and text."""
		# Normalize text by stripping whitespace to improve the cache hit rate.
		normalizedText = text.strip()
		keyString = f"{langFrom}:{langTo}:{normalizedText}"
		return hashlib.md5(keyString.encode("utf-8")).hexdigest()

	def get(self, key: str) -> str | None:
		"""Retrieves a cached translation, or None if not found."""
		return self._cache.get(key)

	def set(self, key: str, value: str) -> None:
		"""Stores a translation result in the cache and persists to disk."""
		self._cache[key] = value
		self._save()

	def getItemCount(self) -> int:
		"""Returns the number of entries in the cache."""
		return len(self._cache)

	def clear(self) -> None:
		"""Removes all entries from the cache and persists the empty state."""
		log.info("Translation cache cleared.")
		self._cache = {}
		self._save()
