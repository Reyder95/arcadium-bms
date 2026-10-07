import { useNavigate, useParams } from "react-router";
import { useAuth } from "../hooks/useAuth"
import { useEffect, useState } from "react";
import { api, calculateDivision, determineTier, divisionProgress, waitForJob } from "../util/helpers";
import { type Job, type ChartRating, type JobResultMatchSubmit, type Match, type MatchSubmit, type Tier, type UserRating } from "../util/NetworkModels";
import { QueueIcon } from "../Components/Home/QueueCard";
import { formatTime, useCountdown } from "../hooks/useCountdown";
import { Button } from "@headlessui/react";
import { LogOut, Send } from "lucide-react";
import { MatchWinDialog } from "../Components/Match/MatchWinDialog";

export default function MatchPage() {

    type SubmitStatus = "idle" | "submitting" | "verifying" | "done" | "error"

    const {user, loading} = useAuth();
    const { id } = useParams();
    const navigate = useNavigate();

    const [status, setStatus] = useState<SubmitStatus>("idle");
    const [message, setMessage] = useState<string | null>(null);

    const [showWin, setShowWin] = useState<boolean>(false);
    const [matchResult, setMatchResult] = useState<string>("lose");

    const [match, setMatch] = useState<Match | null>();
    const [tiers, setTiers] = useState<Tier[]>([]);

    const { msLeft, finished } = useCountdown(match?.cutoff_time)

    useEffect(() => {
        Promise.all([
            api<Match>(`/match/${id}`),
            api<Tier[]>("/info/tiers")
        ])
        .then(([match, tiers]) => {
            setMatch(match)
            setTiers(tiers)

            console.log(match)
        })
    }, [user?.id, id])

    const playerRating : UserRating = { 
        ladder:  match?.ladder ?? "ec",
        display_rating: match?.player_placed_before ? match.player_display_before : -1,
        placed: match?.player_placed_before ?? false,
        games_played: -1,
        rank: -1,
        total: -1,
        wins: -1,
        losses: -1
    }

    const chartRating : ChartRating = {
        ladder: match?.ladder ?? "ec",
        rating: match?.chart_rating_before ?? -1,
        rd: -1,
        games_played: -1,
        wins: -1
    }

    if (loading || !match || tiers.length === 0) {
        return <div className="flex-1 flex items-center justify-center text-muted">Loading…</div>
    }

    const tierIndex: number | null = determineTier(tiers, playerRating.display_rating)
    const division: number | null = calculateDivision(tiers, playerRating.display_rating, tierIndex ?? -1);
    const progress: any | null = divisionProgress(tiers, playerRating.display_rating, tierIndex ?? -1);

    const chartTierIndex: number | null = determineTier(tiers, chartRating.rating)
    const chartDivision: number | null = calculateDivision(tiers, chartRating.rating, chartTierIndex ?? -1);

    const handleSubmit = async () => {
        setStatus("submitting")
        setMessage(null)

        try {
            const matchSubmission = await api<MatchSubmit>(
                `/match/submit`,
                { method: "POST" }
            );

            setStatus("verifying");
            const completed_job: Job<JobResultMatchSubmit> = await waitForJob<JobResultMatchSubmit>(matchSubmission.job_id);
            setStatus("done");

            if (completed_job.result)
            {
                if (completed_job.result.result != null)
                {
                    setMatchResult(completed_job.result.result)
                    setShowWin(true)
                }
            }
        } catch (err) {
            setStatus("error");
            setMessage(err instanceof Error ? err.message : "Something went wrong")
        }
    }

    const handleForfeit = async () => {
        api<Match>(`/match/forfeit`, {method: "POST"})
        .then(() => {
            navigate(`/prep/${match.game}/${match.playtype}/${match.ladder}`)
        })
        .catch(err => console.log(err.message));
    }

    const handleSkip = async () => {
        api<Match>(`/match/skip`, {method: "POST"})
        .then(match => {
            navigate(`/match/${match.id}`)
        })
        .catch(err => console.log(err))
    }

    return (
        <div className="flex-1 flex flex-col items-center justify-center">
            <MatchWinDialog
            open={showWin}
            win={matchResult === "win" ? true : false}
            onClose={() => {
                setShowWin(false);
                navigate("/")
            }}
            ratingChange={0}/>

            <div>
                <p className="uppercase font-archivo text-center font-light text-2xl tracking-widest mb-8">
                    BMS EASY CLEAR MATCH 
                    
                    {
                        match.status === "active" ?
                        <span className="text-green-800"> ACTIVE</span> :
                        <span className="text-red-800"> INACTIVE</span>
                    }

                </p>

                <p className="uppercase font-archivo text-center font-light text-2xl tracking-widest mb-8">
                    {formatTime(msLeft)}
                </p>
            </div>
            <div className="w-1/2 bg-foreground p-5 rounded-md flex flex-row gap-7 relative">
                <div className="absolute -right-3 -top-3">
                    <Button
                    onClick={handleForfeit}
                    aria-label="Cancel match"
                    className="inline-flex size-10 items-center justify-center rounded-full bg-red-800
                                data-hover:bg-red-700 data-active:scale-95
                                data-focus:outline-2 data-focus:outline-highlight
                                data-disabled:opacity-50 transition
                                cursor-pointer"
                    >
                        <LogOut className="size-5" />
                    </Button>
                </div>
                <div className="w-full grid grid-cols-3 gap-x-7 gap-y-20 items-center justify-items-center">
                    <p className="font-bold font-sanchez tracking-widest text-subtext">YOU</p>
                    <p className="col-span-2 font-sanchez font-bold text-xl tracking-wide text-subtext text-center">
                        {match.chart.artist} - {match.chart.title} {match.chart.subtitle ?? ""}
                    </p>

                    <QueueIcon
                        tierIndex={tierIndex}
                        division={division}
                        progress={progress}
                        tiers={tiers}
                        displayProgress={false}
                        displayRating={true}
                    />
                    <div className="col-span-2">
                        <QueueIcon
                        tierIndex={chartTierIndex}
                        division={chartDivision}
                        progress={0}
                        tiers={tiers}
                        displayProgress={false}
                        displayRating={true}
                        />
                    </div>
                <div className="col-span-3 w-full flex justify-end">
                    <div className="flex flex-row gap-5">
                        <Button onClick={handleSkip} className="font-sanchez inline-flex items-center gap-2 bg-zinc-500 brightness-80 hover:brightness-100 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Skip <Send className="size-4"/></Button>
                        <Button onClick={handleSubmit} className="font-sanchez inline-flex items-center gap-2 bg-highlight brightness-80 hover:brightness-100 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Submit <Send className="size-4"/></Button>
                    </div>
                </div>
                </div>

            </div>
        </div>
    )
}