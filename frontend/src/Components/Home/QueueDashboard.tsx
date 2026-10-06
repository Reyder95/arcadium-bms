import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import QueueCard from "./QueueCard";
import { type UserRating, type Tier } from "../../util/NetworkModels";
import { api } from "../../util/helpers";

export default function QueueDashboard() {

    const { user, loading } = useAuth();

    const [ratings, setRatings] = useState<UserRating[]>([])
    const [tiers, setTiers] = useState<Tier[]>([])
    const[error, setError] = useState<string | null>()

    useEffect(() => {
        if (!user) return;

        Promise.all([
            api<UserRating[]>("/users/me/ratings"),
            api<Tier[]>("/info/tiers")
        ])
        .then(([ratings, tiers]) => {
            setRatings(ratings);
            setTiers(tiers);
        })
        .catch(err => setError(err.message))
    }, [user])

    return loading ? (
        <></> ) : (
        <>
            <div className="flex items-center gap-5 justify-center w-full bg-foreground p-5">
                {
                    ratings.map(rating => (
                        <QueueCard 
                        key={rating.ladder}
                        rating={rating} 
                        tiers={tiers}
                        />
                    ))
                }
            </div>
        </>
    )

}