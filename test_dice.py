#!/usr/bin/env python
"""Test the dice parser with various expressions."""
from dice_cog import DiceParser, DiceRoller

TEST_CASES = [
    # Basic rolls
    ("1d6", 1, 6, None, None, None, None, None, 0),
    ("2d20", 2, 20, None, None, None, None, None, 0),
    # Modifiers
    ("1d20+5", 1, 20, None, None, None, None, None, 5),
    ("2d6-3", 2, 6, None, None, None, None, None, -3),
    # Keep highest/lowest
    ("4d6kh3", 4, 6, 3, None, None, None, None, 0),
    ("4d6kl2", 4, 6, None, 2, None, None, None, 0),
    # Drop highest/lowest
    ("4d6dh1", 4, 6, None, None, 1, None, None, 0),
    ("4d6dl1", 4, 6, None, None, None, 1, None, 0),
    # Exploding
    ("1d6!", 1, 6, None, None, None, None, 6, 0),
    ("1d10!8", 1, 10, None, None, None, None, 8, 0),
    # Combined
    ("2d20kh1+5", 2, 20, 1, None, None, None, None, 5),
    ("4d6dl1-2", 4, 6, None, None, None, 1, None, -2),
    ("1d6!+3", 1, 6, None, None, None, None, 6, 3),
]

def test_parsing():
    print("Testing DiceParser...")
    passed = 0
    failed = 0

    for expr_str, num, sides, kh, kl, dh, dl, expl_val, mod in TEST_CASES:
        try:
            expressions = DiceParser.parse(expr_str)
            if len(expressions) != 1:
                print(f"  ❌ {expr_str}: expected 1 expression, got {len(expressions)}")
                failed += 1
                continue

            expr = expressions[0]
            checks = [
                ("num_dice", expr.num_dice, num),
                ("sides", expr.sides, sides),
                ("keep_highest", expr.keep_highest, kh),
                ("keep_lowest", expr.keep_lowest, kl),
                ("drop_highest", expr.drop_highest, dh),
                ("drop_lowest", expr.drop_lowest, dl),
                ("explode_on", expr.explode_on, expl_val),
                ("modifier", expr.modifier, mod),
            ]

            ok = True
            for name, actual, expected in checks:
                if actual != expected:
                    print(f"  ❌ {expr_str}: {name} = {actual}, expected {expected}")
                    ok = False

            if ok:
                print(f"  ✅ {expr_str}")
                passed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ❌ {expr_str}: {e}")
            failed += 1

    print(f"\nParsing: {passed} passed, {failed} failed")

def test_compound():
    print("\nTesting compound expressions...")
    compound_cases = [
        "2d6+1d4",
        "2d6+1d4-3",
        "1d20+1d6+5",
        "4d6kh3+1d4",
    ]

    for expr_str in compound_cases:
        try:
            expressions = DiceParser.parse(expr_str)
            print(f"  ✅ {expr_str} -> {len(expressions)} expressions")
            for e in expressions:
                print(f"      {e.num_dice}d{e.sides} mod={e.modifier}")
        except Exception as e:
            print(f"  ❌ {expr_str}: {e}")

def test_rolling():
    print("\nTesting rolling...")
    test_expr = "4d6kh3"
    expressions = DiceParser.parse(test_expr)
    DiceRoller.roll_expression(expressions[0])
    expr = expressions[0]

    print(f"  Expression: {test_expr}")
    print(f"  Rolls: {[f'{r.value}{' 💥' if r.exploded else ''}{' (dropped)' if not r.kept else ''}' for r in expr.rolls]}")
    print(f"  Kept: {[r.value for r in expr.kept_rolls]}")
    print(f"  Dropped: {[r.value for r in expr.dropped_rolls]}")
    print(f"  Total: {expr.total} (modifier: {expr.modifier})")
    print(f"  ✅ Roll completed")

def test_errors():
    print("\nTesting error cases...")
    error_cases = [
        "0d6",      # Zero dice
        "1d0",      # Zero sides
        "101d6",    # Too many dice
        "1d1001",   # Too many sides
        "2d6kh3",   # Keep more than rolled
        "2d6dh2",   # Drop all
        "1d6!1",    # Explode on 1
        "1d6!7",    # Explode above sides
        "2d6kh1kl1", # Both keep
    ]

    for expr_str in error_cases:
        try:
            DiceParser.parse(expr_str)
            print(f"  ❌ {expr_str}: should have raised ValueError")
        except ValueError:
            print(f"  ✅ {expr_str}: correctly rejected")

if __name__ == "__main__":
    test_parsing()
    test_compound()
    test_rolling()
    test_errors()
    print("\n🎲 All tests complete!")