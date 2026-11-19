'''
Created on 2026/02/13

@author: sin
'''

import time
import timeit
from functools import wraps
from typing import Callable, List, Tuple

import random

# Sample functions to benchmark

# Decorator for simple timing
def time_function(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        print(f"{func.__name__} took {elapsed:.6f} seconds")
        return result
    return wrapper


# Method 1: Simple time.perf_counter() approach
    #
    # n = 30
    #
    # start = time.perf_counter()
    # result1 = fibonacci_recursive(n)
    # time1 = time.perf_counter() - start
    #
    # start = time.perf_counter()
    # result2 = fibonacci_iterative(n)
    # time2 = time.perf_counter() - start
    #
    # start = time.perf_counter()
    # result3 = fibonacci_memoized(n)
    # time3 = time.perf_counter() - start
    
    # print(f"Recursive:   {time1:.6f}s (result: {result1})")
    # print(f"Iterative:   {time2:.6f}s (result: {result2})")
    # print(f"Memoized:    {time3:.6f}s (result: {result3})")


# Method 2: Using timeit module (more robust for small operations)
    
    # n = 25
    # number = 5  # Run each function 5 times
    #
    # time1 = timeit.timeit(
    #     lambda: fibonacci_recursive(n),
    #     number=number
    # )
    #
    # time2 = timeit.timeit(
    #     lambda: fibonacci_iterative(n),
    #     number=number
    # )
    #
    # time3 = timeit.timeit(
    #     lambda: fibonacci_memoized(n),
    #     number=number
    # )
    #
    # print(f"Recursive (5 runs):  {time1:.6f}s (avg: {time1/number:.6f}s)")
    # print(f"Iterative (5 runs):  {time2:.6f}s (avg: {time2/number:.6f}s)")
    # print(f"Memoized (5 runs):   {time3:.6f}s (avg: {time3/number:.6f}s)")



# Method 3: Custom benchmark class
# class FunctionBenchmark:
#     def __init__(self):
#         self.results: List[Tuple[str, float]] = []
#
#     def benchmark(self, func: Callable, *args, **kwargs) -> float:
#         """Benchmark a single function call"""
#         start = time.perf_counter()
#         result = func(*args, **kwargs)
#         elapsed = time.perf_counter() - start
#         self.results.append((func.__name__, elapsed))
#         return elapsed
#
#     def compare(self, functions: List[Tuple[Callable, tuple]], runs: int = 1):
#         """Compare multiple functions"""
#         print("=" * 60)
#         print(f"Method 3: Custom Benchmark Class ({runs} runs)")
#         print("=" * 60)
#
#         for func, args in functions:
#             total_time = 0
#             for _ in range(runs):
#                 total_time += self.benchmark(func, *args)
#
#             avg_time = total_time / runs
#             print(f"{func.__name__:15} | Total: {total_time:.6f}s | Avg: {avg_time:.6f}s")
#
#         # Calculate relative speeds
#         times = [elapsed for _, elapsed in self.results]
#         fastest_time = min(times)
#         print("\nRelative Speed (vs fastest):")
#         for (name, elapsed), (fname, _) in zip(self.results, [f for f, _ in functions]):
#             speedup = elapsed / fastest_time
#             print(f"  {name:15} {speedup:.2f}x")
#         print()


# Method 4: Multiple iterations with statistics
# def compare_with_statistics():
#     print("=" * 60)
#     print("Method 4: Multiple iterations with statistics")
#     print("=" * 60)
#
#     n = 25
#     iterations = 10
#
#     times_recursive = []
#     times_iterative = []
#     times_memoized = []
#
#     for _ in range(iterations):
#         start = time.perf_counter()
#         fibonacci_recursive(n)
#         times_recursive.append(time.perf_counter() - start)
#
#         start = time.perf_counter()
#         fibonacci_iterative(n)
#         times_iterative.append(time.perf_counter() - start)
#
#         # Clear cache for each iteration
#         fibonacci_memoized.cache_clear() if hasattr(fibonacci_memoized, 'cache_clear') else None
#         start = time.perf_counter()
#         fibonacci_memoized(n, {})
#         times_memoized.append(time.perf_counter() - start)
#
#     def print_stats(name: str, times: List[float]):
#         avg = sum(times) / len(times)
#         min_t = min(times)
#         max_t = max(times)
#         print(f"{name:15} | Avg: {avg:.6f}s | Min: {min_t:.6f}s | Max: {max_t:.6f}s")
#
#     print_stats("Recursive", times_recursive)
#     print_stats("Iterative", times_iterative)
#     print_stats("Memoized", times_memoized)
#     print()

#@staticmethod
def popcount(intval): 
    BITS_COUNT_TABLE = [ 0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, ]
    cnt = 0
    while intval > 0 :
        cnt += BITS_COUNT_TABLE[intval & 0x0f]
        intval >> 4
        cnt += BITS_COUNT_TABLE[intval & 0x0f]
        intval >> 4
    return cnt
    
#@staticmethod
def bitlength_shift(val):
    counter = 0
    while True :
        nib = val & 0x0f
        val >>= 4
        if val != 0 :
            counter += 4
            continue
        counter += (0, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4 )[nib]
        break
    return counter
    
def bitlength_bin(n):
    return len(f'{n:b}')
    
if __name__ == "__main__":
    #compare_with_perf_counter()
    number = 1000  # Run each function 5 times
    
    rand = random.Random()

    rand.seed(1)
    time1 = timeit.timeit(
        lambda: [bitlength_bin(rand.randint(1,2**16)) for _ in range(number)],
        number=number
    )
    
    rand.seed(1)
    time2 = timeit.timeit(
        lambda: [bitlength_shift(rand.randint(1,2**16)) for _ in range(number)],
        number=number
    )
        
    rand.seed(1)
    time3 = timeit.timeit(
        lambda: [rand.randint(1,2**16).bit_length() for _ in range(number)],
        number=number
    )

    print(f"bin ({number} runs):  {time1:.6f}s (avg: {time1/number:.6f}s)")
    print(f"shift ({number} runs):  {time2:.6f}s (avg: {time2/number:.6f}s)")
    print(f"bit_length ({number} runs):  {time3:.6f}s (avg: {time3/number:.6f}s)")
    print()
    # benchmark = FunctionBenchmark()
    # benchmark.compare([
    #     (fibonacci_recursive, (25,)),
    #     (fibonacci_iterative, (25,)),
    #     (fibonacci_memoized, (25,)),
    # ], runs=5)
    #
    # compare_with_statistics()