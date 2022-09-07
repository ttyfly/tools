from typing import List


def argmin(arr: float) -> int:
    min_val = arr[0]
    min_i = 0
    for i, num in enumerate(arr):
        if num < min_val:
            min_val = num
            min_i = i
    return min_i


def argmax(arr: float) -> int:
    max_val = arr[0]
    max_i = 0
    for i, num in enumerate(arr):
        if num > max_val:
            max_val = num
            max_i = i
    return max_i


def argmin_all(arr: float) -> List[int]:
    min_val = arr[0]
    min_i = [0]
    for i, num in enumerate(arr):
        if num == min_val:
            min_i.append(i)
        elif num < min_val:
            min_val = num
            min_i = [i]
    return min_i


def argmax_all(arr: float) -> List[int]:
    max_val = arr[0]
    max_i = [0]
    for i, num in enumerate(arr):
        if num == max_val:
            max_i.append(i)
        elif num > max_val:
            max_val = num
            max_i = [i]
    return max_i


def quote(string: str) -> str:
    return string.replace(' ', '%20')


def unquote(string: str) -> str:
    return string.replace('%20', ' ')
