# -*- coding: utf-8 -*-

def splitText(text: str, maxLength: int) -> list[str]:
	"""
	Splits text into chunks of at most maxLength characters using a recursive approach.
	Attempts to split at natural boundaries like paragraphs, sentences, and words.
	"""
	if maxLength <= 0 or len(text) <= maxLength:
		return [text]

	def _split(currentText: str, separators: list[str]) -> list[str]:
		if len(currentText) <= maxLength:
			return [currentText]
		if not separators:
			return [currentText[i:i+maxLength] for i in range(0, len(currentText), maxLength)]
		
		sep = separators[0]
		if sep == '':
			return [currentText[i:i+maxLength] for i in range(0, len(currentText), maxLength)]
			
		chunks = currentText.split(sep)
		newChunks = []
		for i, chunk in enumerate(chunks):
			if i < len(chunks) - 1:
				newChunks.append(chunk + sep)
			else:
				if chunk:
					newChunks.append(chunk)
					
		result = []
		currentChunk = ""
		
		for c in newChunks:
			if len(c) > maxLength:
				if currentChunk:
					result.append(currentChunk)
					currentChunk = ""
				# Recursively split the oversized chunk with remaining separators
				subChunks = _split(c, separators[1:])
				result.extend(subChunks)
			else:
				if len(currentChunk) + len(c) <= maxLength:
					currentChunk += c
				else:
					if currentChunk:
						result.append(currentChunk)
					currentChunk = c
					
		if currentChunk:
			result.append(currentChunk)
			
		return result

	return _split(text, ['\n\n', '\n', '. ', '。', ' ', ''])
