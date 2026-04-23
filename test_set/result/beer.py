#!/usr/bin/env python
# By GvR, demystified after a version by Fredrik Lundh.

import sys

# Define constants for better readability and maintainability
NUM_BOTTLES = 100
DEFAULT_NUM_BOTTLES = 100
TAKEN_DOWN = "Take one down, pass it around,"
NO_MORE_BOTTLES = "no more bottles of beer"
ONE_BOTTLE = "one bottle of beer"

def bottle(n: int) -> str:
    """Return the correct bottle string based on the number of bottles."""
    if n == 0:
        return NO_MORE_BOTTLES
    if n == 1:
        return ONE_BOTTLE
    return f"{n} bottles of beer"

def main() -> None:
    """Print the beer song for the given number of bottles."""
    num_bottles = DEFAULT_NUM_BOTTLES
    if sys.argv[1:]:
        try:
            num_bottles = int(sys.argv[1])
        except ValueError:
            print("Error: Input must be an integer.")
            return

    for i in range(num_bottles):
        print(bottle(num_bottles - i), "on the wall,", sep="")
        print(bottle(num_bottles - i), sep="")
        print(TAKEN_DOWN)
        print(bottle(num_bottles - i - 1), "on the wall.", sep="")

if __name__ == "__main__":
    main()