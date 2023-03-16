"""Collection of generators"""


# Sieve of Eratosthenes
# Based on code by David Eppstein, UC Irvine, 28 Feb 2002
# http://code.activestate.com/recipes/117119/
def gen_primes():
    """Generate an infinite sequence of prime numbers."""
    # Maps composites to primes witnessing their compositeness.
    # This is memory efficient, as the sieve is not "run forward"
    # indefinitely, but only as long as required by the current
    # number being tested.
    sieve = {}

    # The running integer that's checked for primeness
    current = 2

    while True:
        if current not in sieve:
            # current is a new prime.
            # Yield it and mark its first multiple that isn't
            # already marked in previous iterations
            yield current
            sieve[current * current] = [current]
        else:
            # current is composite. sieve[current] is the list of primes that
            # divide it. Since we've reached current, we no longer
            # need it in the map, but we'll mark the next
            # multiples of its witnesses to prepare for larger
            # numbers
            for composite in sieve[current]:
                sieve.setdefault(composite + current, []).append(composite)
            del sieve[current]

        current += 1
