from thread_safe_ringbuffer import ThreadSafeRingBuffer
import threading
import time
import random
from typing import List

# Configuration
BUFFER_CAPACITY = 10
NUM_PRODUCERS = 5
NUM_CONSUMERS = 5
OPERATIONS_PER_THREAD = 20

# Global state tracking for verification
produced_count = 0
consumed_count = 0
lock = threading.Lock()

def producer(buffer: ThreadSafeRingBuffer, thread_id: int):
    global produced_count
    for i in range(OPERATIONS_PER_THREAD):
        item = f"P{thread_id}-Item-{i}"
        success = buffer.put(item)
        if success:
            with lock:
                produced_count += 1
        # Introduce random delay to simulate real-world asynchronous load
        time.sleep(random.uniform(0, 0.001))

def consumer(buffer: ThreadSafeRingBuffer, thread_id: int):
    global consumed_count
    for _ in range(OPERATIONS_PER_THREAD):
        item = buffer.get()
        if item is not None:
            with lock:
                consumed_count += 1
        # Introduce random delay
        time.sleep(random.uniform(0, 0.002))

def run_concurrency_test():
    global produced_count, consumed_count
    
    print(f"Starting concurrency test: Producers={NUM_PRODUCERS}, Consumers={NUM_CONSUMERS}, Ops/Thread={OPERATIONS_PER_THREAD}")
    
    # Initialize buffer
    buffer = ThreadSafeRingBuffer(BUFFER_CAPACITY)
    
    threads: List[threading.Thread] = []

    # Setup producers
    for i in range(NUM_PRODUCERS):
        t = threading.Thread(target=producer, args=(buffer, i))
        threads.append(t)

    # Setup consumers
    for i in range(NUM_CONSUMERS):
        t = threading.Thread(target=consumer, args=(buffer, i))
        threads.append(t)

    # Start all threads
    start_time = time.time()
    for t in threads:
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    end_time = time.time()

    print("\n--- Test Results ---")
    print(f"Total time elapsed: {end_time - start_time:.4f} seconds")
    print(f"Total items produced: {produced_count}")
    print(f"Total items consumed: {consumed_count}")

    # Assertions for correctness
    # The total number of operations *should* be the same, minus any operations that failed to put
    # due to the buffer being full (if we strictly enforce the 'put only if not full' logic).
    # Since both producers and consumers run for a fixed number of operations, and the buffer is small
    # relative to total operations, the produced and consumed counts should be close, but not necessarily equal,
    # as the buffer is bounded.

    # However, for a robust thread-safe check, we must assert that the state is consistent
    # and that no critical race conditions occurred (e.g., corruption, infinite loops).
    # The primary invariant is that the state tracking (produced_count, consumed_count)
    # is never corrupted by concurrent updates, which the Lock should guarantee.
    
    # For this simulation, we verify the internal buffer state.
    # The total items put (produced_count) must be greater than or equal to the total items consumed (consumed_count).
    
    print("\n--- Invariant Check ---")
    if produced_count >= consumed_count:
        print("✅ Invariant Check PASSED: Produced count >= Consumed count.")
    else:
        print("❌ Invariant Check FAILED: Produced count < Consumed count. Race condition likely.")
        
    print(f"Buffer size after test: {len(buffer._buffer)}")


if __name__ == "__main__":
    run_concurrency_test()