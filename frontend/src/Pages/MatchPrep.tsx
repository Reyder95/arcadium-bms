import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import QueueCard from "../Components/Home/QueueCard";
import type { CanQueue, Tier, TierData, UserRating } from "../util/NetworkModels";
import { api } from "../util/helpers";
import { useParams } from "react-router";

export default function MatchPrep() {
    const { user, loading } = useAuth();
    const { game, playtype, ladder } = useParams();

    const [rating, setRating] = useState<UserRating[]>([])
    const [tiers, setTiers] = useState<Tier[]>([])
    const [canQueue, setCanQueue] = useState<CanQueue>({can_queue: false})
    const [error, setError] = useState<string>();

    useEffect(() => {
        console.log("Effect ran!")
        if (!user) return;

        Promise.all([
            api<UserRating[]>(`/users/me/ratings/${game}/${playtype}/${ladder}`),
            api<TierData>("/info/tiers"),
            api<CanQueue>("/users/me/can-queue")
        ])
        .then(([rating, tiers, canQueue]) => {
            setRating(rating);
            setTiers(tiers.tiers);
            setCanQueue(canQueue)
            console.log(tiers);
        })
        .catch(err => {
            console.log(err.message)
            setError(err.message)
        })
    }, [user])

    const unrankedUserRating : UserRating = { 
        ladder:  ladder ?? "ec",
        display_rating: -1,
        placed: false,
        games_played: rating.length == 0 ? -1 : rating[0].games_played,
        rank: -1,
        total: rating.length == 0 ? 0 : rating[0].total,
        wins: rating.length == 0 ? 0 : rating[0].wins,
        losses: rating.length == 0 ? 0 : rating[0].losses
    }
    
    if (loading || tiers.length === 0) {
        return <div className="flex-1 flex items-center justify-center text-muted">Loading…</div>
    }

    return (
        <div className="flex-1 flex items-center justify-center">
            {
                rating.length == 0 ? ( <QueueCard rating={unrankedUserRating} tiers={tiers} /> ) : (<QueueCard rating={rating[0].placed ? rating[0] : unrankedUserRating} displayProgress={rating[0].placed ? true : false} tiers={tiers}/>)
            }
        </div>
    )
}