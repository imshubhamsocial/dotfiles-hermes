from ring_buffer import BasicRingBuffer
import threading
from typing import Any

class ThreadSafeRingBuffer(BasicRingBuffer):
    """
    Thread-safe implementation of the RingBuffer using threading locks.
    Inherits from BasicRingBuffer to reuse core logic.
    """
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._lock = threading.Lock()

    def put(self, item: Any) -> bool:
        """
        Adds an item to the buffer atomically.
        Returns True on success, False if full.
        """
        with self._lock:
            return super().put(item)

    def get(self) -> Any | None:
        """
        Removes and returns an item from the buffer atomically.
        Returns None if empty.
        """
        with self._lock:
            return super().get()

    # is_full and is_empty are atomic enough that explicit locks are often
    # unnecessary unless they are used for complex coordination, but
    # for strict consistency with state changes, they should be locked.
    def is_full(self) -> bool:
        """Checks if the buffer is currently full atomically."""
        with self._lock:
            return super().is_full()

    def is_empty(self) -> bool:
        """Checks if the buffer is currently empty atomically."""
        with self._lock:
            return super().is_empty()

# Note: For a more complex producer/consumer model where threads block
# waiting for space/items, threading.Condition would be required,
# but for basic thread safety (preventing race conditions on state reads/writes),
# a Lock is sufficient for Milestone 2.
