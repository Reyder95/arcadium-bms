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
import ForegroundCard from "../Components/General/ForegroundCard";
import ProgressBar from "../Components/General/ProgressBar";

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

    const { msLeft, finished, skipFinished, skipMsLeft } = useCountdown(match?.cutoff_time, match?.start_time)

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
        <div className="w-full flex-1 flex flex-col">
            <MatchWinDialog
            open={showWin}
            win={matchResult === "win" ? true : false}
            onClose={() => {
                setShowWin(false);
                navigate("/")
            }}
            ratingChange={0}/>

            <div className="flex-1 flex flex-col">
                <div className="w-full mx-auto flex-1 flex flex-col items-center justify-center">
                    <div className="w-1/2 flex flex-row justify-between mb-8">
                        <div>
                            <p className="font-archivo tracking-[0.2em] text-subtext text-sm mb-3">BMS 7K &middot; EASY CLEAR &middot; <span className="text-highlight">RANKED</span></p>
                            <h1 className="font-archivo text-5xl tracking-widest font-thin">Match #{id}</h1>
                        </div>
                        <div>
                            <h1 className="font-mono text-5xl tracking-widest font-bold mb-3">10:40</h1>
                            <p className="font-sanchez text-subtext text-right">Cutoff 4:00 PM</p>
                        </div>
                    </div>
                    <div className="w-1/2 mb-8">
                        <ProgressBar
                        value={75}
                        />
                    </div>
                    <div className="w-1/2 grid grid-cols-3 gap-10 mx-auto">
                        <ForegroundCard className="text-center">
                            <p className="font-archivo font-thin tracking-[0.2em] text-subtext">YOU</p>
                            <QueueIcon
                                tierIndex={tierIndex}
                                division={division}
                                progress={progress}
                                tiers={tiers}
                                displayProgress={true}
                                displayRating={true}
                            />
                        </ForegroundCard>
                        <ForegroundCard className="text-center">
                            <p className="font-archivo font-thin tracking-[0.2em] text-subtext">POTENTIAL CHANGE</p>   
                            <div className="flex-1 flex flex-col items-center justify-center gap-2">
                                <div className="grid grid-cols-2 divide-x divide-zinc-700/60">
                                <div className="px-8 text-center">
                                    <p className="font-mono text-5xl font-bold text-green-400">+18</p>
                                    <p className="mt-3 text-subtext font-sanchez">Easy clear or better</p>
                                </div>
                                <div className="px-8 text-center">
                                    <p className="font-mono text-5xl font-bold text-red-400">−14</p>
                                    <p className="mt-3 text-subtext font-sanchez">No clear by cutoff</p>
                                </div>
                                </div>

                            </div>        
                        </ForegroundCard>
                        <ForegroundCard className="text-center w-full">
                            <p className="font-archivo font-thin tracking-[0.2em] text-subtext">OPPONENT</p>
                            <QueueIcon
                                tierIndex={tierIndex}
                                division={division}
                                progress={progress}
                                tiers={tiers}
                                displayProgress={false}
                                displayRating={true}
                            />

                            <p
                            className="mt-4 line-clamp-2 wrap-break-word font-sanchez text-subtext font-bold tracking-widest w-full"
                            title={`${match.chart.title} ${match.chart.subtitle ?? ""}`}
                            >
                            {match.chart.title} {match.chart.subtitle} 
                            </p> 

                            <p className="mt-2 truncate font-sanchez text-subtext tracking-widest" title={match.chart.artist}>
                            {match.chart.artist}
                            </p>

                            <div className="flex flex-row w-full justify-center gap-3 mt-3">
                                <p className="font-semibold bg-background px-2 py-1 rounded-xl border border-zinc-600">sl3</p>
                                <p className="font-semibold bg-background px-2 py-1 rounded-xl border border-zinc-600">★3</p>
                            </div>
                        </ForegroundCard>
                    </div>
                    <div className="w-1/2 mt-5">
                        <ForegroundCard>
                            <div className="flex flex-row justify-between items-center">
                                <div className="flex flex-row items-center gap-5">
                                    <span className="size-3 rounded-full bg-red-500"></span>
                                    <div className="flex flex-col">
                                        <div>
                                            <p className="font-sanchez font-bold">No clear yet!</p>
                                        </div>
                                        <div>
                                            <p className="font-sanchez text-subtext">Click on <em>check scores</em> to check <em>Bokutachi</em> for recent scores!</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-row gap-4">
                                    <Button className="font-sanchez bg-foreground border border-zinc-600/80 rounded-lg p-3 font-bold">Skip &middot; <span className="text-subtext text-sm">30s left</span></Button>
                                    <Button className="font-sanchez bg-highlight rounded-lg p-3 font-bold">Check Scores</Button>
                                </div>
                            </div>
                        </ForegroundCard>
                    </div>
                    <div className="w-1/2 mt-5">
                        <ForegroundCard className="border-2 border-dotted border-zinc-500/50 flex-row items-center gap-5">
                            <p className="font-sanchez font-bold shrink-0">
                                Load it in game!
                            </p>
                            <p className="font-sanchez text-subtext text-[13px] flex-1 leading-7">
                                Press <span className="bg-background p-1 border m-1">F2</span> on your table in Beatoraja or press <span className="bg-background p-1 border m-1">F8</span> in openLR2 to reload your match table!
                            </p>
                            <p className="font-mono bg-background p-2 border border-zinc-500 text-subtext shrink-0">
                                https://arcadium.com/api/match/{match.user.id}/table
                            </p>
                            <div className="flex flex-row gap-4">
                                <Button className="text-highlight underline tracking-wide">Download Chart</Button>
                                <Button className="text-red-400 underline tracking-wide">Forfeit</Button>
                            </div>
                        </ForegroundCard>
                    </div>
                </div>

            </div>


            {/* <div>
                <p className="uppercase font-archivo text-center font-light text-2xl tracking-widest mb-8">
                    
                    {
                        match.ladder == "ec" ? "BMS EAASY CLEAR MATCH" : "BMS HARD CLEAR MATCH"
                    }
                    
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
            <div className="w-1/2 bg-background-dark border-zinc-500 border p-5 rounded-md flex flex-row gap-7 relative">
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
                        <Button disabled={skipFinished} onClick={handleSkip} className="font-sanchez inline-flex items-center gap-2 bg-zinc-500 brightness-80 hover:brightness-100 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Skip <Send className="size-4"/></Button>
                        <Button onClick={handleSubmit} className="font-sanchez inline-flex items-center gap-2 bg-highlight brightness-80 hover:brightness-100 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Submit <Send className="size-4"/></Button>
                    </div>
                </div>
                </div> */}
            
        </div>
    )
}