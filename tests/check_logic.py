"""Regression checks for 集合论/数理逻辑.tex (not a formal proof checker).

Run from any directory: python tests/check_logic.py
Requires Python 3.10+ and NumPy: python -m pip install numpy
Finite truth-table/model checks complement, but do not replace, the proofs.
"""
from __future__ import annotations

from collections import Counter
from itertools import product
from pathlib import Path
import re

try:
    import numpy as np
except ImportError as exc:
    raise SystemExit("NumPy is required: python -m pip install numpy") from exc

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "集合论" / "数理逻辑.tex"
CHECKS: Counter[str] = Counter()


def check(condition: object, name: str, group: str = "semantics") -> None:
    if not bool(np.all(condition)):
        raise AssertionError(name)
    CHECKS[group] += 1


def imp(a: object, b: object) -> np.ndarray:
    return np.logical_or(np.logical_not(a), b)


def nand(a: object, b: object) -> np.ndarray:
    return np.logical_not(np.logical_and(a, b))


def nor(a: object, b: object) -> np.ndarray:
    return np.logical_not(np.logical_or(a, b))


def check_source() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    check(not re.search(r"TODO", text, re.I), "unanswered TODO", "source")
    # % escaped by an odd number of backslashes is not a comment.
    active_lines: list[str] = []
    for line in text.splitlines():
        for pos, char in enumerate(line):
            if char == "%":
                n = 0
                k = pos - 1
                while k >= 0 and line[k] == "\\":
                    n += 1
                    k -= 1
                if n % 2 == 0:
                    line = line[:pos]
                    break
        active_lines.append(line)
    active = "\n".join(active_lines)
    stack: list[tuple[str, int]] = []
    envs: Counter[str] = Counter()
    for match in re.finditer(r"\\(begin|end)\{([^}]+)\}", active):
        action, env = match.groups()
        if action == "begin":
            stack.append((env, match.end()))
            envs[env] += 1
        else:
            check(bool(stack) and stack[-1][0] == env,
                  f"unbalanced environment {env} at {match.start()}", "source")
            _, begin = stack.pop()
            body = active[begin:match.start()]
            if env in {"theorem", "proposition", "corollary", "lemma", "property"}:
                check(r"\begin{proof}" in body,
                      f"missing proof in {env} at {begin}", "source")
            if env == "example":
                check(any(r"\begin{" + e + "}" in body for e in ("proof", "solution")),
                      f"unanswered example at {begin}", "source")
            if env == "align*":
                for row in body.split(r"\\"):
                    check(row.count("&") <= 1, "multiple align columns", "source")
    check(not stack, "unclosed environment", "source")
    labels = re.findall(r"\\label\{([^}]+)\}", active)
    check(len(labels) == len(set(labels)), "duplicate label", "source")
    refs = re.findall(r"\\(?:[cC]ref|eqref|ref)\{([^}]+)\}", active)
    for group in refs:
        for label in group.split(","):
            check(label.strip() in labels, f"undefined local reference {label}", "source")
    check(r"\documentclass" not in active and r"\usepackage" not in active,
          "chapter acquired a preamble", "source")
    check(not re.search(r"\\(?:def|edef|NewDocumentCommand|DeclareMathOperator)\b", active),
          "chapter defines commands", "source")
    # The corrected schema must retain the missing quantifier variable and B(y).
    check(r"(\exists x)(\exists y)[A(x)\limp B(y)]" in active,
          "exercise 4.4 6(3) regression", "source")
    check(r"example:数理逻辑.全称实例化" in labels, "instantiation label", "source")
    print("Source environments:", dict(sorted(envs.items())))
    print("TODO: 0; local labels:", len(labels))


def check_propositional() -> None:
    vals = np.array(list(product([False, True], repeat=3)), dtype=bool)
    a, b, c = vals.T
    equations = {
        "double negation": (~~a, a),
        "or idempotence": (a | a, a),
        "and idempotence": (a & a, a),
        "or commutativity": (a | b, b | a),
        "and commutativity": (a & b, b & a),
        "or associativity": ((a | b) | c, a | (b | c)),
        "and associativity": ((a & b) & c, a & (b & c)),
        "or absorption": (a | (a & b), a),
        "and absorption": (a & (a | b), a),
        "or distribution": (a | (b & c), (a | b) & (a | c)),
        "and distribution": (a & (b | c), (a & b) | (a & c)),
        "excluded middle": (a | ~a, np.ones(8, dtype=bool)),
        "contradiction": (a & ~a, np.zeros(8, dtype=bool)),
        "De Morgan or": (~(a | b), ~a & ~b),
        "De Morgan and": (~(a & b), ~a | ~b),
        "or zero": (a | False, a),
        "and one": (a & True, a),
        "or one": (a | True, np.ones(8, dtype=bool)),
        "and zero": (a & False, np.zeros(8, dtype=bool)),
        "xor/iff": (a ^ b, ~(a == b)),
        "implication": (imp(a, b), ~a | b),
        "iff": (a == b, imp(a, b) & imp(b, a)),
        "xor symmetry": (a ^ b, b ^ a),
        "xor associativity": ((a ^ b) ^ c, a ^ (b ^ c)),
        "contraposition": (imp(a, b), imp(~b, ~a)),
        "negated iff": (~(a == b), a == ~b),
        "nand negation": (nand(a, a), ~a),
        "nor negation": (nor(a, a), ~a),
        "nand and": (nand(nand(a, b), nand(a, b)), a & b),
        "nor and": (nor(nor(a, a), nor(b, b)), a & b),
        "nand or": (nand(nand(a, a), nand(b, b)), a | b),
        "nor or": (nor(nor(a, b), nor(a, b)), a | b),
        "iff symmetry": (a == b, b == a),
        "iff associativity": ((a == b) == c, a == (b == c)),
        "iff DNF": (a == b, (a & b) | (~a & ~b)),
        "common consequent": (imp(a, c) & imp(b, c), imp(a | b, c)),
        "common antecedent": (imp(a, b) & imp(a, c), imp(a, b & c)),
        "conditional proof": (imp(a, imp(b, c)), imp(a & b, c)),
        "normal-form DNF": (imp(a, b) == c, (a & ~b & ~c) | (~a & c) | (b & c)),
        "normal-form CNF": (imp(a, b) == c, (a | c) & (~b | c) & (~a | b | ~c)),
    }
    for name, (left, right) in equations.items():
        check(left == right, name, "propositional")
    for name, op in (("imp", imp), ("nand", nand), ("nor", nor)):
        check(np.any(op(a, op(b, c)) != op(op(a, b), c)),
              name + " nonassociativity", "propositional")
    rules = [imp(a & b, a), imp(a, a | b), imp(a & b, a & b),
             imp((a | b) & ~a, b), imp(imp(a, b) & a, b),
             imp(imp(a, b) & ~b, ~a),
             imp(imp(a, b) & imp(b, c), imp(a, c)),
             imp((a | b) & imp(a, c) & imp(b, c), c)]
    for index, rule in enumerate(rules):
        check(rule, f"inference rule {index}", "propositional")
    p, q, r, t = np.array([0, 1, 1, 0], dtype=bool)
    check(imp(p, imp(q & r, t)) and not imp(imp(p, q & r), t),
          "explicit bracket counterexample", "propositional")
    formula = imp(~a | b, c)
    check(formula.any() and not formula.all(), "contingent formula", "propositional")
    def f(p: object, q: object, r: object) -> np.ndarray:
        return (~np.asarray(p) | ~np.asarray(q) | ~np.asarray(r)) & (np.asarray(p) | ~np.asarray(q) | ~np.asarray(r)) & (np.asarray(p) | ~np.asarray(q) | np.asarray(r))
    check(f(a, a, a) == ~a, "ternary f negation", "propositional")
    check(f(~a, ~a, ~b) == (a | b), "ternary f disjunction", "propositional")
    check(f(a, b, c) == np.array([1, 1, 0, 0, 1, 1, 1, 0], dtype=bool),
          "original ternary truth table", "propositional")
    # Check every truth function on three variables, including both constants.
    minterms = np.all(vals[:, None, :] == vals[None, :, :], axis=2)
    maxterms = ~minterms
    check(minterms.sum(axis=0) == 1, "minterm uniqueness", "normal forms")
    check((~maxterms).sum(axis=0) == 1, "maxterm uniqueness", "normal forms")
    for bits in product([False, True], repeat=8):
        truth = np.array(bits, dtype=bool)
        # Empty reduction is tested as a truth-function convention only.
        dnf = np.any(minterms[:, truth], axis=1)
        cnf = np.all(maxterms[:, ~truth], axis=1)
        check(dnf == truth, "principal DNF", "normal forms")
        check(cnf == truth, "principal CNF", "normal forms")


def check_predicate() -> None:
    for n in range(1, 4):
        predicates = [np.array(v, dtype=bool) for v in product([False, True], repeat=n)]
        for a, b in product(predicates, repeat=2):
            eqs = [
                (~np.all(a), np.any(~a)), (~np.any(a), np.all(~a)),
                (np.all(a & b), np.all(a) & np.all(b)),
                (np.any(a | b), np.any(a) | np.any(b)),
                (np.all(a[:, None] | b[None, :]), np.all(a) | np.all(b)),
                (np.any(a[:, None] & b[None, :]), np.any(a) & np.any(b)),
                (np.any(imp(a[:, None], b[None, :])), imp(np.all(a), np.any(b))),
                (np.all(imp(a[:, None], b[None, :])), imp(np.any(a), np.all(b))),
                (np.any(imp(a, b)), imp(np.all(a), np.any(b))),
            ]
            for left, right in eqs:
                check(left == right, f"quantifier identity n={n}", "predicate")
            check(imp(np.all(a) | np.all(b), np.all(a | b)), "forall or implication", "predicate")
            check(imp(np.any(a & b), np.any(a) & np.any(b)), "exists and implication", "predicate")
            check(imp(np.all(imp(a, b)) & np.any(a), np.any(b)), "existential elimination", "predicate")
            for const in (False, True):
                for op in (np.logical_and, np.logical_or):
                    for quant in (np.all, np.any):
                        check(quant(op(a, const)) == op(quant(a), const), "scope extension", "predicate")
        for cells in product([False, True], repeat=n*n):
            relation = np.array(cells, dtype=bool).reshape(n, n)
            allall = np.all(np.all(relation, axis=1))
            existsall = np.any(np.all(relation, axis=1))
            all_exists = np.all(np.any(relation, axis=1))
            all_y_exists_x = np.all(np.any(relation, axis=0))
            existsexists = np.any(relation)
            check(allall == np.all(np.all(relation, axis=0)), "forall interchange", "predicate")
            check(existsexists == np.any(np.any(relation, axis=0)), "exists interchange", "predicate")
            check(imp(existsall, all_y_exists_x), "exists forall -> forall exists", "predicate")
            check(imp(allall, all_exists), "forall forall -> forall exists", "predicate")
            check(imp(all_exists, existsexists), "forall exists -> exists exists", "predicate")
    a = np.array([True, False]); b = ~a
    check(np.all(a | b) and not (np.all(a) or np.all(b)), "forall or countermodel", "countermodels")
    check(not np.any(a & b) and np.any(a) and np.any(b), "exists and countermodel", "countermodels")
    relation = np.eye(2, dtype=bool)
    check(np.all(np.any(relation, axis=1)) and not np.any(np.all(relation, axis=0)),
          "mixed quantifier countermodel", "countermodels")
    zero = np.zeros(2, dtype=bool)
    check(np.any(imp(a, zero)) and not imp(np.any(a), np.any(zero)),
          "exercise 4-22(2)", "countermodels")
    check(a[0] and not np.all(a), "UG missing eigenparameter", "countermodels")
    check(np.any(a) and not a[1], "ES arbitrary constant", "countermodels")
    phi = np.array([True, False, False])
    check(np.count_nonzero(phi) == 1, "unique existence example", "countermodels")
    check(not np.all(imp(phi[:, None] == phi[None, :], np.eye(3, dtype=bool))),
          "incorrect unique-existence encoding", "countermodels")
    empty = np.array([], dtype=bool)
    check(not imp(np.all(empty), np.any(empty)), "nonempty-domain requirement", "countermodels")
    x = np.arange(-10, 11, dtype=np.int64)
    check(x > (x-4)+3, "real inequality witness sample", "countermodels")
    check(~(x+3 > x+3), "real inequality refutation sample", "countermodels")


def main() -> None:
    check_source()
    check_propositional()
    check_predicate()
    print("PASS:", dict(CHECKS), "total", sum(CHECKS.values()))
    print("Finite semantic checks do not prove unrestricted first-order validity.")


if __name__ == "__main__":
    main()
