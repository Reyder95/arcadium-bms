export interface UserRating {
    ladder: string;
    display_rating: number;
    placed: boolean;
    games_played: number;
    rank: number;
    total: number;
    wins: number;
    losses: number; 
}

export interface Tier {
    name: string;
    floor: number;
}