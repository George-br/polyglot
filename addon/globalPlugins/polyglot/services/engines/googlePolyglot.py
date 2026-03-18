# -*- coding: utf-8 -*-

import html
import json

import addonHandler
from logHandler import log

from ...common import languages
from ..engine import BaseHttpEngine
from ...common.exceptions import ApiResponseError, AuthenticationError

addonHandler.initTranslation()


class GoogleHQApiError(ApiResponseError):
	pass


class GoogleHQTranslateEngine(BaseHttpEngine):
	id = "googlePolyglot"
	name = _("Google Translate (Polyglot)")

	@property
	def autoDetectCode(self) -> str | None:
		return "auto"

	@property
	def defaultTargetLanguage(self) -> str:
		return "zh-CN"

	def getSupportedLanguages(self) -> dict:
		supportedCodes = [
			"auto",
			"af",
			"sq",
			"ar",
			"hy",
			"az",
			"eu",
			"be",
			"bn",
			"bs",
			"bg",
			"ca",
			"ceb",
			"ny",
			"zh-CN",
			"zh-TW",
			"co",
			"hr",
			"cs",
			"da",
			"nl",
			"en",
			"eo",
			"et",
			"tl",
			"fi",
			"fr",
			"fy",
			"gl",
			"ka",
			"de",
			"el",
			"gu",
			"ht",
			"ha",
			"haw",
			"he",
			"hi",
			"hmn",
			"hu",
			"is",
			"ig",
			"id",
			"ga",
			"it",
			"ja",
			"jw",
			"kn",
			"kk",
			"km",
			"ko",
			"ku",
			"ky",
			"lo",
			"la",
			"lv",
			"lt",
			"lb",
			"mk",
			"mg",
			"ms",
			"ml",
			"mt",
			"mi",
			"mr",
			"mn",
			"my",
			"ne",
			"no",
			"ps",
			"fa",
			"pl",
			"pt",
			"pa",
			"ro",
			"ru",
			"sm",
			"gd",
			"sr",
			"st",
			"sn",
			"sd",
			"si",
			"sk",
			"sl",
			"so",
			"es",
			"su",
			"sw",
			"sv",
			"tg",
			"ta",
			"te",
			"th",
			"tr",
			"uk",
			"ur",
			"uz",
			"vi",
			"cy",
			"xh",
			"yi",
			"yo",
			"zu",
		]
		return languages.getLanguageDictForCodes(supportedCodes)

	def getConfigSpec(self) -> list[dict]:
		spec = super().getConfigSpec()
		spec.extend(
			[
				{"id": "apiKey", "label": _("Mirror Token"), "type": "password", "default": ""},
				{
					"id": "customUrl",
					"label": _("Endpoint URL"),
					"type": "text",
					"default": "https://translate.googleapis.mirror.nvdadr.com/polyglotGoogle",
				},
			]
		)
		return spec

	def _buildRequestParams(self, text: str, langFrom: str, langTo: str, config: dict) -> dict:
		mirrorToken = config.get("apiKey", "3a64ad20-724b-41dc-ba23-cf64185dbfa3").strip()
		if not mirrorToken:
			raise AuthenticationError(_("Mirror Token for Google Translate (HQ) is not configured."))
		url = config.get("customUrl", "https://translate.googleapis.mirror.nvdadr.com/polyglotGoogle").strip()
		bodyData = [[[text], langFrom, langTo], "wt_lib"]
		headers = {
			"Content-Type": "application/json+protobuf",
			"User-Agent": "NVDAPolyglot/1.0",
			"X-Mirror-Token": mirrorToken,
		}
		return {
			"method": "POST",
			"url": url,
			"headers": headers,
			"data": json.dumps(bodyData).encode("utf-8"),
		}

	def _parseResponse(self, responseBody: str) -> dict:
		"""
		Parses the simple, nested array response returned by the endpoint
		when receiving a protobuf-style request.
		Expected format: [["Translated text..."], ["detected_lang_code"]]
		"""
		try:
			data = json.loads(responseBody)
		except json.JSONDecodeError:
			raise GoogleHQApiError(_("Failed to parse API response."))
		try:
			rawTranslatedText = data[0][0]
			translatedText = html.unescape(rawTranslatedText)
		except (IndexError, TypeError):
			if isinstance(data, dict) and "error" in data:
				errorMsg = data["error"].get("message", "Unknown API error")
				raise GoogleHQApiError(errorMsg)
			log.error(f"Could not parse Google HQ response. Raw: {responseBody}")
			raise GoogleHQApiError(_("Invalid API response or no translation text included."))
		detectedLang = None
		if len(data) > 1 and isinstance(data[1], list) and data[1]:
			detectedLang = data[1][0]
		return {"translation": translatedText, "langDetected": detectedLang}
