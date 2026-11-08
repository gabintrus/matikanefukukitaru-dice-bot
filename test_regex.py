import re

# Include trailing modifier
pattern = re.compile(r'(?<!\w)(\d+d\d+(?:[^a-z\s]*(?:[a-z]+\d+)?(?:!\d*)?(?:[+-]\d+)?)?)', re.IGNORECASE)

tests = ['roll 1d6', 'roll 1d20+5', 'roll 2d6+1d4', 'roll 2d6+1d4-3', 'roll 2d6+1d4+2', 'roll 4d6kh3', 'roll 2d20kh1', 'roll 1d6!', 'roll 2d20kh1+2']
for t in tests:
    m = pattern.search(t)
    if m:
        print(f'{t:20s} -> {m.group(1)}')
    else:
        print(f'{t:20s} -> NO MATCH')