import math

from app.models import PlayerRating, ChartRating

SEED_RD = {
    "sg": 120,
    "other": 225
}

TIERS = [
    ( "Copper", 100 ),
    ( "Bronze", 500 ),
    ( "Silver", 900 ),
    ( "Gold", 1300 ),
    ( "Platinum", 1900 ),
    ( "Emerald", 2500 ),
    ( "Diamond", 3000 ),
    ( "Master", 3400 ),
    ( "Grandmaster", 3800 )
]

DIVISIONS = 5

ELO_BASE = 100
ELO_PER_LEVEL = 100
ELO_FLOOR = 100

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
    return max(ELO_FLOOR, ELO_BASE + ELO_PER_LEVEL * sieg)

# --- GLICKO2 FUNCTIONS ---

def new_volatility(sigma, phi, v, delta):
    a = math.log(sigma**2)

    def f(x):
        ex = math.exp(x)
        return (ex * (delta**2 - phi**2 - v - ex)) / (2 * (phi**2 * v + ex) ** 2) - (x - a) / TAU**2

    A = a

    if delta**2 > phi**2 + v:
        B = math.log(delta**2 - phi**2 - v)
    else:
        k = 1
        while(f(a - k * TAU)) < 0:
            k += 1
        B = a - k * TAU

    fA, fB = f(A), f(B)

    while abs(B - A) > EPSILON:
        C = A + (A - B) * fA / (fB - fA)
        fC = f(C)
        if fC * fB <= 0:
            A, fA = B, fB
        else:
            fA /= 2
        B, fB = C, fC

    return math.exp(A/2)

if __name__ == "__main__":
    print(rank_for(1000))