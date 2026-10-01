DEFAULT_VOLATILITY = 0.06

SEED_RD = {
    "sg": 120,
    "other": 225
}

TIERS = [
    ( "Copper", 100 ),
    ( "Bronze", 400 ),
    ( "Silver", 600 ),
    ( "Gold", 800 ),
    ( "Platinum", 1100 ),
    ( "Emerald", 1400 ),
    ( "Diamond", 1650 ),
    ( "Master", 1850 ),
    ( "Grandmaster", 2050 )
]

DIVISIONS = 5

def calculate_division(elo, index):
    if index == len(TIERS) - 1:
        return None

    division_width = (TIERS[index+1][1] - TIERS[index][1]) / DIVISIONS

    steps = int((elo - TIERS[index][1]) // division_width)
    steps = max(0, min(steps, DIVISIONS - 1))

    return DIVISIONS - steps



def rank_for(elo):
    index = 0
    for i in reversed(range(len(TIERS))):
        if elo >= TIERS[i][1]:
            index = i
            break

    return { 
        "tier": TIERS[index], 
        "division": calculate_division(elo, index)
        }

def sieg_to_elo(sieg):
    return max(100, 200 + 50 * sieg)

if __name__ == "__main__":
    print(rank_for(1000))