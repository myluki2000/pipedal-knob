from typing import TypeVar, Generic, Callable

T = TypeVar("T")

class Event(Generic[T]):
    """
    C#-style event class for Python.
    This class allows you to create events that can have multiple handlers
    attached to them. You can add and remove handlers, and when the event
    is triggered, all attached handlers will be called with the provided
    arguments.

    Example usage:
        event = Event()
        
        def handler(arg):
            print(f"Handler called with arg: {arg}")
        
        event += handler
        event.trigger("Hello, World!")  # This will call the handler with "Hello, World!"
        
        event -= handler
        event.trigger("This will not be printed")  # No handlers are attached, so nothing happens.
    """

    def __init__(self):
        self.handlers = []

    def add_listener(self, handler: Callable[[T], None]) -> "Event[T]":
        self.handlers.append(handler)
        return self
    
    def remove_listener(self, handler: Callable[[T], None]) -> "Event[T]":
        self.handlers.remove(handler)
        return self

    def __call__(self, arg: T) -> None:
        for handler in self.handlers:
            handler(arg)