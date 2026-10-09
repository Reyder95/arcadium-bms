export interface TierProgressData {
    tierIndex: number;
    division: number;
    progress: number;
}

export interface BetweenTierData {
    startingProgress: TierProgressData;
    endingProgress: TierProgressData
}