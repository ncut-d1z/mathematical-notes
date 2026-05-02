(* Independent symbolic checks. Run: wolframscript -file tests/check_logic.wl
   This file is supplied for Mathematica/Wolfram Engine; no kernel is assumed.
   Finite or propositional checks are not proofs of all first-order schemata. *)
ClearAll[p, q, r, x, y, f];
identities = {
 Equivalent[Implies[p, q], Or[Not[p], q]],
 Equivalent[Implies[p, q], Implies[Not[q], Not[p]]],
 Equivalent[Equivalent[Equivalent[p, q], r], Equivalent[p, Equivalent[q, r]]],
 Equivalent[Xor[Xor[p, q], r], Xor[p, Xor[q, r]]],
 Equivalent[Nand[p, p], Not[p]],
 Equivalent[Nor[p, p], Not[p]],
 Equivalent[Nand[Nand[p, q], Nand[p, q]], And[p, q]],
 Equivalent[Nor[Nor[p, p], Nor[q, q]], And[p, q]],
 Equivalent[Nand[Nand[p, p], Nand[q, q]], Or[p, q]],
 Equivalent[Nor[Nor[p, q], Nor[p, q]], Or[p, q]],
 Equivalent[Implies[p, Implies[q, r]], Implies[And[p, q], r]],
 Equivalent[Equivalent[Implies[p, q], r],
   Or[And[p, Not[q], Not[r]], And[Not[p], r], And[q, r]]],
 Equivalent[Equivalent[Implies[p, q], r],
   And[Or[p, r], Or[Not[q], r], Or[Not[p], q, Not[r]]]]
};
If[!And @@ (TautologyQ[#, {p, q, r}] & /@ identities), Exit[1]];
nonAssociative = {
 Equivalent[Implies[p, Implies[q, r]], Implies[Implies[p, q], r]],
 Equivalent[Nand[p, Nand[q, r]], Nand[Nand[p, q], r]],
 Equivalent[Nor[p, Nor[q, r]], Nor[Nor[p, q], r]]
};
If[Or @@ (TautologyQ[#, {p, q, r}] & /@ nonAssociative), Exit[1]];
f[p_, q_, r_] := And[Or[Not[p], Not[q], Not[r]],
 Or[p, Not[q], Not[r]], Or[p, Not[q], r]];
If[!TautologyQ[Equivalent[f[p, p, p], Not[p]], {p}], Exit[1]];
If[!TautologyQ[Equivalent[f[Not[p], Not[p], Not[q]], Or[p, q]], {p, q}], Exit[1]];
If[!TrueQ[FullSimplify[x > (x - 4) + 3, Element[x, Reals]]], Exit[1]];
If[!TrueQ[FullSimplify[Not[y + 3 > y + 3], Element[y, Reals]]], Exit[1]];
Print["PASS: symbolic propositional identities, counterexamples and real witnesses."];
