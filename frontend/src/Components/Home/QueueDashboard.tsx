import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import QueueCard from "./QueueCard";
import { type UserRating } from "../../util/NetworkModels";
import { api } from "../../util/helpers";

export default function QueueDashboard() {

    const { user, loading } = useAuth();

    const [ratings, setRatings] = useState<UserRating[]>([])
    const[error, setError] = useState<string | null>()

    useEffect(() => {
        if (!user) return;

        Promise.all([
            api<UserRating[]>("/users/me/ratings")
        ])
        .then(([ratings]) => {
            setRatings(ratings);
        })
        .catch(err => setError(err.message))
    }, [user])

    return loading ? (
        <></> ) : (
        <>
            <div className="flex items-center gap-5 justify-center w-full bg-foreground p-5">
                {
                    ratings.map(rating => (
                        <QueueCard rating={rating} />
                    ))
                }
            </div>
        </>
    )

}