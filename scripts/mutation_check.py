#!/usr/bin/env python3
"""Non-vacuity check for the Halmos proofs.

Injects seven bugs, one at a time, into src/EnforcedToken.sol, runs the relevant Halmos check, and
requires a counterexample. The original source is always restored, even on error.

Usage: python3 scripts/mutation_check.py      (from the repository root; ~1-2 min)
Exit code 0 iff every mutant is killed.
"""
import re
import subprocess
import sys
from pathlib import Path

SRC = Path("src/EnforcedToken.sol")

MUTANTS = [
    ("frozen sender may transfer", "check_transfer",
     "if (f.status != ACTIVE) revert Restricted(from);",
     "if (f.status == BLOCKED) revert Restricted(from);"),
    ("seize does not reduce held", "check_seize",
     "x.held -= uint120(amt);", ""),
    ("burn does not reduce supply", "check_burnFromHold",
     "totalSupply -= amt;", ""),
    ("hold not bounded by spendable balance", "check_placeHold",
     "if (uint256(x.held) + amt > x.balance) revert HoldExceedsSpendable();", ""),
    ("seize deletes a different hold record", "check_seize",
     "if (h.amount == 0) delete holds[id];",
     "if (h.amount == 0) delete holds[bytes32(uint256(id) + 1)];"),
    ("blockBatch wipes the account's balance", "check_blockBatch",
     "_acct[accounts[i]].status = BLOCKED;",
     "_acct[accounts[i]] = Account(0, 0, BLOCKED);"),
    ("ordinary transfer advances the compliance log", "check_transfer",
     "        emit Transfer(from, to, amt);\n    }\n\n    // ================================================================ compliance actions",
     "        logCount += 1;\n        emit Transfer(from, to, amt);\n    }\n\n    // ================================================================ compliance actions"),
]


def halmos(function: str) -> str:
    subprocess.run(["forge", "clean"], check=True, capture_output=True)
    r = subprocess.run(["halmos", "--contract", "HalmosProofs", "--function", function],
                       capture_output=True, text=True)
    return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout + r.stderr)


def main() -> int:
    original = SRC.read_text()
    killed = 0
    try:
        for name, fn, old, new in MUTANTS:
            if original.count(old) != 1:
                print(f"[ERROR] pattern for '{name}' not found exactly once")
                return 2
            SRC.write_text(original.replace(old, new, 1))
            out = halmos(fn)
            ok = "Counterexample" in out or "[FAIL]" in out
            killed += ok
            print(f"[{'KILLED' if ok else 'SURVIVED'}] {name}  ({fn})")
    finally:
        SRC.write_text(original)
        subprocess.run(["forge", "clean"], capture_output=True)
    print(f"{killed}/{len(MUTANTS)} mutants killed")
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
