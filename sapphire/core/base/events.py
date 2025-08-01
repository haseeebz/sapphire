from typing import Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Union
import threading

@dataclass(frozen = True)
class Chain():
	"""
	An event's identifier giving insight on:
	1) What caused the event (via flow)
	2) Where the root event orignally started from (via context)

	Context is the absolute origin of an event. Context 0 is used for sapphire itself while
	all contexts after that are reserved for clients.
	This same context id is used by Sapphire Server to route response events to clients that
	sent it.

	Flow is the actual 'chain of events'. Events with the same flow (and obviously context) are in
	the same chain.
	"""

	context: int
	flow: int

	def __str__(self) -> str:
		return f"({self.context}:{self.flow})"
	
	def __repr__(self) -> str:
		return self.__str__()
	
	def __eq__(self, other) -> bool:
		return (self.context, self.flow) == (other.context, other.flow)
	

class SapphireEvents():
	"""
	All Sapphire Events and helper functions.
	"""

	Chain = Chain
	_lock = threading.Lock()
	_intern_chain = Chain(0, 0)
	_current_context = 0
	_intern_map: dict[str, type["Event"]] = {}

	@classmethod
	def chain(cls, event: Union["Event", None] = None) -> Chain:
		"Class Method to chain events. If None, returns a new chain."
		if isinstance(event, cls.Event):
			return event.chain
		else:
			chain = cls._intern_chain
			with cls._lock: 
				cls._intern_chain = Chain(
					0,
					chain.flow + 1
				)
			return chain
		
		
	@classmethod
	def new_context_chain(cls) -> Chain:
		"Method for getting a chain with a new context."
		with cls._lock: cls._current_context += 1
		chain = Chain(
			cls._current_context, 0
		)
		return chain
	

	@classmethod
	def make_timestamp(cls):
		"Class method for giving a standard timestamp format for all events."
		return datetime.now().strftime("%H:%M:%S")
			

	
	@classmethod
	def serialize(cls, event: str) -> type["Event"]:
		"Method for getting an event class using its name. Will raise an exception on invalid values."

		if not cls._intern_map:
			for name, attr in SapphireEvents.__dict__.items():

				if not isinstance(attr, type): continue

				if issubclass(attr, SapphireEvents.Event):
					cls._intern_map[name] = attr

		if event not in cls._intern_map:
			raise ValueError(f"Unknown event: {event}")
		return cls._intern_map[event]
		


	@dataclass(frozen = True)
	class Event():
		"Base event class."
		sender: str
		timestamp: str 
		chain: Chain


	@dataclass(frozen = True)
	class InitCompleteEvent(Event):
		"An event passed just before the main loop starts."
		pass


	@dataclass(frozen = True)
	class LogEvent(Event):
		"Event that the logger module listens for."
		level: Literal["debug", "info", "warning", "critical"]
		message: str


	@dataclass(frozen = True)
	class ShutdownEvent(Event):
		"Sent to core to intiate a shutdown."
		emergency: bool
		situation: Literal["request", "failure", "critical", "user"]
		message: str = ""


	@dataclass(frozen = True)
	class UserInputEvent(Event):
		"All user messages are sent using this event."
		message: str


	@dataclass(frozen = True)
	class CommandRegisterEvent(Event):
		"Sent to command handler to register a command"
		module: str
		cmd: str
		info: str
		func: Callable[[list[str], "SapphireEvents.Chain"], str]


	@dataclass(frozen = True)
	class CommandEvent(Event):
		"Command that the command handler can execute."
		module: str
		cmd: str
		args: list[str]


	@dataclass(frozen = True)
	class CommandExecutedEvent(Event):
		"The output of an executed command."
		cmd: tuple[str, str, list[str]]
		success: bool
		output: str


	@dataclass(frozen = True)
	class ConfirmationEvent(Event):
		"Used for confirmation with the user."
		message: str
		options: list[str]
		selected: str | None


	@dataclass(frozen = True)
	class ErrorEvent(Event):
		"In case something goes wrong."
		error: str
		message = str 


	@dataclass(frozen = True)
	class PromptEvent(Event):
		"Event passed by the prompt manager after it assembles the prompt"
		content: str


	@dataclass(frozen = True)
	class AIResponseEvent(Event):
		"The response generated by the AI model."
		message: str
		extras: dict[str, Any]

	
	@dataclass(frozen = True)
	class ClientActivationEvent(Event):
		"The first event passed by the server to the client so it can initialize its chain."
		message: str

	
	@dataclass(frozen= True)
	class TaskRegisterEvent(Event):
		"Event passed to task manager to register an new task."
		module: str
		name: str
		args: list[str]
		info: str
		func: Callable[[list[str], Chain], str]


	@dataclass(frozen= True)
	class TaskEvent(Event):
		"Start a new task."
		module: str
		name: str
		args: list[str]


	@dataclass(frozen= True)
	class TaskCompletionEvent(Event):
		"The result of a task."
		module: str
		name: str
		args: list[str]
		success: bool
		output: str

	@dataclass(frozen = True)
	class TaskMapUpdatedEvent(Event):

		active_mods: dict[str, list[tuple[str, str, list[str]]]]
		# ke
	


