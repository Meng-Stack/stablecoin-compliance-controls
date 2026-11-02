# Requires: Foundry (forge), Python 3 with requirements.txt installed.
.PHONY: all build test bench data plot clean

all: test bench plot

build:
	forge build

# Correctness: unit tests + stateful invariant fuzzing
test:
	forge test --mc "Security|Invariants"

# Gas benchmarks. --isolate is REQUIRED: each top-level call is metered as its own transaction.
bench:
	forge test --isolate --mc Bench

# Regenerate SMT trees and proofs (~2 minutes for N = 1e5)
data:
	python3 scripts/gen_smt.py 1 10 100 1000 10000 100000

plot:
	python3 scripts/plot.py results

clean:
	forge clean
