# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import wx
from configobj.validate import is_boolean

# Create a Type Alias for complex, reused types.
ConfigSpec = dict[str, Any]
ConfigSection = dict[str, Any]


class ControlHandlerBase(ABC):
	@property
	@abstractmethod
	def configType(self) -> str:
		pass

	@abstractmethod
	def formatConfigDefault(self, value: Any) -> str:
		pass

	@abstractmethod
	def createControlPair(
		self,
		panel: wx.Window,
		spec: ConfigSpec,
	) -> tuple[wx.StaticText | None, wx.Control]:
		pass

	@abstractmethod
	def getValueFromControl(self, control: wx.Control) -> Any:
		pass

	@abstractmethod
	def setValueToControl(self, control: wx.Control, value: Any, spec: ConfigSpec):
		pass

	@abstractmethod
	def bindEvent(self, control: wx.Control, callback: Callable[[wx.Event], None]):
		"""Binds the appropriate 'value changed' event to the control."""
		pass

	def updateControlState(
		self,
		control: wx.Control,
		labelControl: wx.StaticText | None,
		prop: str,
		value: Any,
	):
		if prop == "enabled":
			if control.IsEnabled() != value:
				control.Enable(bool(value))
				if labelControl:
					labelControl.Enable(bool(value))
		elif prop == "visible":
			isShown = control.IsShown()
			if isShown != value:
				control.Show(bool(value))
				if labelControl:
					labelControl.Show(bool(value))

	@abstractmethod
	def loadFromConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec):
		"""Loads a value from the config dictionary and applies it to the control."""
		pass

	@abstractmethod
	def saveToConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec):
		"""Gets the value from the control and saves it to the config dictionary."""
		pass


_controlRegistry: dict[str, ControlHandlerBase] = {}


def registerControl(typeName: str) -> Callable[[type[ControlHandlerBase]], type[ControlHandlerBase]]:
	"""Class decorator that registers a control handler for the given config type name."""

	def decorator(cls: type[ControlHandlerBase]) -> type[ControlHandlerBase]:
		if typeName in _controlRegistry:
			raise ValueError(f"Control type '{typeName}' is already registered.")
		_controlRegistry[typeName] = cls()
		return cls

	return decorator


def getControlHandler(typeName: str) -> ControlHandlerBase:
	"""Returns the registered control handler for the given config type name."""
	if typeName not in _controlRegistry:
		raise ValueError(f"Unknown control type: '{typeName}'")
	return _controlRegistry[typeName]


@registerControl("checkbox")
class CheckboxHandler(ControlHandlerBase):
	@property
	def configType(self) -> str:
		return "boolean"

	def formatConfigDefault(self, value: Any) -> str:
		return str(bool(value)).capitalize()

	def createControlPair(
		self,
		panel: wx.Window,
		spec: ConfigSpec,
	) -> tuple[wx.StaticText | None, wx.Control]:
		control = wx.CheckBox(panel, label=spec["label"])
		return (None, control)

	def getValueFromControl(self, control: wx.Control) -> bool:
		assert isinstance(control, wx.CheckBox)
		return control.IsChecked()

	def setValueToControl(self, control: wx.Control, value: Any, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.CheckBox)
		control.SetValue(is_boolean(value) if value is not None else False)

	def bindEvent(self, control: wx.Control, callback: Callable[[wx.Event], None]) -> None:
		assert isinstance(control, wx.CheckBox)
		control.Bind(wx.EVT_CHECKBOX, callback)

	def loadFromConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.CheckBox)
		value = configSection.get(spec["id"], spec.get("default"))
		self.setValueToControl(control, value, spec)

	def saveToConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.CheckBox)
		configSection[spec["id"]] = self.getValueFromControl(control)


class LabeledControlHandler(ControlHandlerBase, ABC):
	def createControlPair(
		self,
		panel: wx.Window,
		spec: ConfigSpec,
	) -> tuple[wx.StaticText | None, wx.Control]:
		wxClass, kwargs = self.getWxClassAndKwargs(spec)
		label = wx.StaticText(panel, label=spec["label"])
		control = wxClass(panel, **kwargs)
		return (label, control)

	@abstractmethod
	def getWxClassAndKwargs(self, spec: ConfigSpec) -> tuple[type[wx.Control], dict[str, Any]]:
		pass


@registerControl("text")
@registerControl("password")
class TextHandler(LabeledControlHandler):
	@property
	def configType(self) -> str:
		return "string"

	def formatConfigDefault(self, value: Any) -> str:
		return f'"{str(value)}"'

	def getWxClassAndKwargs(self, spec: ConfigSpec) -> tuple[type[wx.Control], dict[str, Any]]:
		kwargs = {"style": wx.TE_PASSWORD} if spec.get("type") == "password" else {}
		return wx.TextCtrl, kwargs

	def getValueFromControl(self, control: wx.Control) -> str:
		assert isinstance(control, wx.TextCtrl)
		return control.GetValue()

	def setValueToControl(self, control: wx.Control, value: Any, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.TextCtrl)
		control.SetValue(str(value) if value is not None else "")

	def bindEvent(self, control: wx.Control, callback: Callable[[wx.Event], None]) -> None:
		assert isinstance(control, wx.TextCtrl)
		control.Bind(wx.EVT_TEXT, callback)

	def loadFromConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.TextCtrl)
		value = configSection.get(spec["id"], spec.get("default"))
		self.setValueToControl(control, value, spec)

	def saveToConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.TextCtrl)
		configSection[spec["id"]] = self.getValueFromControl(control)


@registerControl("choice")
class ChoiceHandler(LabeledControlHandler):
	@property
	def configType(self) -> str:
		return "string"

	def formatConfigDefault(self, value: Any) -> str:
		return f'"{str(value)}"'

	def getWxClassAndKwargs(self, spec: ConfigSpec) -> tuple[type[wx.Control], dict[str, Any]]:
		return wx.Choice, {}

	def getValueFromControl(self, control: wx.Control) -> Any:
		assert isinstance(control, wx.Choice)
		selection = control.GetSelection()
		return control.GetClientData(selection) if selection != wx.NOT_FOUND else None

	def setValueToControl(self, control: wx.Control, value: Any, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.Choice)
		self.populateChoices(control, spec.get("choices", {}), value)

	def updateControlState(
		self,
		control: wx.Control,
		labelControl: wx.StaticText | None,
		prop: str,
		value: Any,
	) -> None:
		assert isinstance(control, wx.Choice)
		if prop == "choices":
			currentSelection = self.getValueFromControl(control)
			self.populateChoices(control, value, currentSelection)
		else:
			super().updateControlState(control, labelControl, prop, value)

	def populateChoices(
		self,
		choiceCtrl: wx.Choice,
		choicesDict: dict[str, str],
		currentValueCode: Any = None,
	) -> None:
		currentChoices = OrderedDict()
		for i in range(choiceCtrl.GetCount()):
			currentChoices[choiceCtrl.GetClientData(i)] = choiceCtrl.GetString(i)

		if choicesDict == currentChoices:
			return

		choiceCtrl.Freeze()
		try:
			if not choicesDict:
				choiceCtrl.Clear()
				choiceCtrl.Disable()
				return
			choiceCtrl.Enable()
			codes, names = list(choicesDict.keys()), list(choicesDict.values())
			choiceCtrl.Clear()
			for i, name in enumerate(names):
				choiceCtrl.Append(name, codes[i])
			finalCode = currentValueCode if currentValueCode in codes else (codes[0] if codes else None)
			if finalCode:
				try:
					index = codes.index(finalCode)
					if choiceCtrl.GetSelection() != index:
						choiceCtrl.SetSelection(index)
				except (ValueError, KeyError):
					if choiceCtrl.GetCount() > 0:
						choiceCtrl.SetSelection(0)
			elif choiceCtrl.GetCount() > 0:
				choiceCtrl.SetSelection(0)
		finally:
			choiceCtrl.Thaw()

	def bindEvent(self, control: wx.Control, callback: Callable[[wx.Event], None]) -> None:
		assert isinstance(control, wx.Choice)
		control.Bind(wx.EVT_CHOICE, callback)

	def loadFromConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.Choice)
		value = configSection.get(spec["id"], spec.get("default"))
		self.setValueToControl(control, value, spec)

	def saveToConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.Choice)
		configSection[spec["id"]] = self.getValueFromControl(control)


@registerControl("spinctrl")
class SpinCtrlHandler(LabeledControlHandler):
	@property
	def configType(self) -> str:
		return "integer"

	def formatConfigDefault(self, value: Any) -> str:
		return str(int(value))

	def getWxClassAndKwargs(self, spec: ConfigSpec) -> tuple[type[wx.Control], dict[str, Any]]:
		kwargs = {
			"value": str(spec.get("default", 15)),
			"min": spec.get("min", 1),
			"max": spec.get("max", 60),
		}
		# wx.SpinCtrl accepts min, max, and initial as constructor arguments.
		return wx.SpinCtrl, {"min": kwargs["min"], "max": kwargs["max"], "initial": int(kwargs["value"])}

	def getValueFromControl(self, control: wx.Control) -> int:
		assert isinstance(control, wx.SpinCtrl)
		return control.GetValue()

	def setValueToControl(self, control: wx.Control, value: Any, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.SpinCtrl)
		try:
			control.SetValue(int(value))
		except (ValueError, TypeError):
			control.SetValue(spec.get("default", control.GetMin()))

	def bindEvent(self, control: wx.Control, callback: Callable[[wx.Event], None]) -> None:
		assert isinstance(control, wx.SpinCtrl)
		# The EVT_SPINCTRL event triggers when the value changes.
		control.Bind(wx.EVT_SPINCTRL, callback)
		# Also bind the text event to respond to direct input.
		control.Bind(wx.EVT_TEXT, callback)

	def loadFromConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.SpinCtrl)
		value = configSection.get(spec["id"], spec.get("default"))
		self.setValueToControl(control, value, spec)

	def saveToConfig(self, control: wx.Control, configSection: ConfigSection, spec: ConfigSpec) -> None:
		assert isinstance(control, wx.SpinCtrl)
		configSection[spec["id"]] = self.getValueFromControl(control)
