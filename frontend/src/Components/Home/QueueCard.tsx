import { useAuth } from "../../hooks/useAuth";

import { Button } from "@headlessui/react";
import { CircleArrowOutUpRight, Podium } from "lucide-react";
import ProgressBar from "../General/ProgressBar";
import { type Match, type Tier, type UserRating } from "../../util/NetworkModels";
import { api, calculateDivision, determineTier, divisionProgress, toRoman, winRate } from "../../util/helpers";
import { returnIcon } from "../../util/rankedIconPicker";
import { useNavigate } from "react-router";

interface QueueCardProps {
    rating: UserRating;
    tiers: Tier[],
    displayProgress?: boolean;
    displayRating?: boolean;
}

interface QueueIconProps {
    tierIndex: number | null;
    division: number | null;
    progress: any | null;
    tiers: Tier[];
    displayProgress?: boolean;
    displayRating?: boolean
}

export function QueueIcon(props: QueueIconProps) {
    return (
    <div className="flex items-center h-ful flex-col gap-4">
        <div className="h-32 flex items-end justify-center">
            {
                props.tierIndex !== null ?
                <img className="h-28 w-auto" src={returnIcon(props.tiers[props.tierIndex].name)}/> :
                <img className="h-28 w-auto" src={returnIcon("Unranked")}/>
            }

        </div>
        <div className="font-archivo items-center font-light text-xl tracking-widest">
            {
            props.tierIndex !== null 
            ? `${props.tiers[props.tierIndex].name} ${props.division ? toRoman(props.division) : ""}`
            : "Unranked"
            }
        </div>
        {
            props.displayRating ? (
            <div className="font-mono text-xl font-extrabold flex items-center gap-3">
                1576 <span className="text-subtext font-light text-[15px]">≈ ☆12.11</span>
            </div>
            ): (<></>)
        }
        
            {
                props.displayProgress ?
                <div className="w-3/4">
                    <ProgressBar
                    value={props.progress?.percent ?? 0}
                    className="bg-highlight w-full" 
                    />
                    <div className="font-sanchez flex flex-row justify-between text-subtext mt-2 text-sm">
                        <p>1540</p>
                        <p>Gold II &middot; 1660</p>
                    </div> 
                    </div>
                    : (<></>)

            }
    </div>
    )

}

export default function QueueCard(props: QueueCardProps) {
    const { user, loading } = useAuth();
    const navigate = useNavigate();

    console.log(props.rating.placed)

    const tierIndex: number | null = determineTier(props.tiers, props.rating.display_rating)
    const division: number | null = calculateDivision(props.tiers, props.rating.display_rating, tierIndex ?? -1);
    const progress: any | null = divisionProgress(props.tiers, props.rating.display_rating, tierIndex ?? -1);

    const MatchType = {
        COMPETITIVE: "competitive",
        CASUAL: "casual"
    }

    type MatchType = (typeof MatchType)[keyof typeof MatchType];

    const handleQueue = async (type: MatchType) => {
        api<Match>(`/match/create?game=bms&playtype=7k&ladder=${props.rating.ladder}&type=${type}`, { method: "POST" })
        .then((match) => {
            navigate(`/match/${match.id}`)
        })
        .catch(err => console.log(err.message))
    }

    return loading ? (
        <></>
    ) : (
        <>
            <div className="w-1/4 bg-background-dark p-5 rounded-md flex flex-col">
                <p className="uppercase font-archivo text-center font-light text-2xl tracking-widest mb-8">
                    {props.rating.ladder == "ec" ? "BMS Easy Clear Ladder" : "BMS Hard Clear Ladder"}
                </p>

                <div className="flex flex-row justify-center items-center">
                    <QueueIcon 
                    tierIndex={tierIndex}
                    division={division}
                    progress={progress}
                    tiers={props.tiers}
                    displayProgress={props.displayProgress}
                    displayRating={props.displayRating}
                    />

                    <div className="flex-1 flex flex-col gap-4 justify-center h-full items-center">
                        <div className="text-center flex flex-col gap-1">
                            <p className="text-xs uppercase tracking-widest text-subtext">Rating</p>
                            <p className="text-3xl font-bold tabular-nums">
                                { props.rating.display_rating !== -1 ?
                                props.rating.display_rating.toFixed(0) :
                                "---"
                                }
                                </p>
                            {
                                props.rating.display_rating !== -1 ?
                                <p className="text-xs text-subtext">#{props.rating.rank} of {props.rating.total}</p> : ""
                            }
                            
                        </div>
                        <div className="text-center flex flex-col gap-1">
                            <p className="text-xs uppercase tracking-widest text-subtext">Record</p>
                            <p className="text-xl font-bold tabular-nums">
                            <span className="text-green-600">{props.rating.wins}W</span> · <span className="text-red-600">{props.rating.losses}L</span>
                            </p>
                            {
                                props.rating.total !== 0 ?
                                <p className="text-xs text-subtext">{winRate(props.rating.wins, props.rating.losses)?.toFixed(2)}% win rate</p> :
                                <p className="text-xs text-subtext">0% win rate</p>             

                            }

                        </div>
                    </div>
                </div>

            <div className="flex flex-row justify-end gap-5 mt-5">
                <div className="">
                    <Button className="font-sanchez inline-flex items-center gap-2 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Queue Casual <CircleArrowOutUpRight className="size-4 font-bold"/></Button>
                </div>

                <div className="text-right">
                    <Button onClick={() => handleQueue(MatchType.COMPETITIVE)} className="font-sanchez inline-flex items-center gap-2 bg-highlight brightness-80 hover:brightness-100 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Queue Ranked <Podium className="size-5 font-bold"/></Button>
                </div>
            </div>

            </div>
        </>
    )
}