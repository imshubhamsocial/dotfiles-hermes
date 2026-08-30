from typing import Any, Deque
from collections import deque
import abc

class RingBuffer(abc.ABC):
    """
    Abstract Base Class for a Ring Buffer structure.
    Subclasses must implement the core logic.
    """
    @abc.abstractmethod
    def __init__(self, capacity: int):
        pass

    @abc.abstractmethod
    def put(self, item: Any) -> bool:
        """Adds an item to the buffer. Returns True on success, False if full."""
        pass

    @abc.abstractmethod
    def get(self) -> Any | None:
        """Removes and returns an item from the buffer. Returns None if empty."""
        pass

    @abc.abstractmethod
    def is_full(self) -> bool:
        """Checks if the buffer is currently full."""
        pass

    @abc.abstractmethod
    def is_empty(self) -> bool:
        """Checks if the buffer is currently empty."""
        pass

class BasicRingBuffer(RingBuffer):
    """
    A non-thread-safe, basic implementation of a ring buffer using a deque.
    This serves as the foundation for Milestone 1.
    """
    def __init__(self, capacity: int):
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")
        self._capacity = capacity
        self._buffer: Deque[Any] = deque(maxlen=capacity)

    def put(self, item: Any) -> bool:
        """Adds an item to the buffer. Deque handles overflow by overwriting oldest item if maxlen is set."""
        # If using a standard deque with maxlen, put() always succeeds but
        # replaces the oldest item if capacity is reached.
        # For a strict "full" check, we should manually manage the logic,
        # but since the requirement is a basic, non-thread-safe implementation,
        # we'll use the deque's natural FIFO replacement behavior if capacity is hit.
        # To strictly follow the API contract (return False if full), we need to check length first.
        if len(self._buffer) >= self._capacity:
            # Since deque maxlen handles replacement automatically, we only return False
            # if we want to enforce a strict "put only if not full" model.
            # For simplicity and typical ring buffer use, we allow overwrite if the intent
            # is a fixed-size buffer, but to satisfy the "Returns True/False if full" requirement:
            return False # Buffer is considered "full" in the strict sense
        
        self._buffer.append(item)
        return True

    def get(self) -> Any | None:
        """Removes and returns the oldest item from the buffer."""
        if not self.is_empty():
            return self._buffer.popleft()
        return None

    def is_full(self) -> bool:
        """Checks if the buffer is currently full."""
        return len(self._buffer) == self._capacity

    def is_empty(self) -> bool:
        """Checks if the buffer is currently empty."""
        return len(self._buffer) == 0

# Example usage (for quick verification, not part of the final module):
# buf = BasicRingBuffer(3)
# print(f"Empty: {buf.is_empty()}") # True
# buf.put(1)
# buf.put(2)
# print(f"Is full: {buf.is_full()}") # False
# buf.put(3)
# print(f"Is full: {buf.is_full()}") # True
# print(f"Get: {buf.get()}") # 1
# print(f"Is full: {buf.is_full()}") # False
