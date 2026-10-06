import { useAuth } from "../../hooks/useAuth";

import { Button } from "@headlessui/react";
import { CircleArrowOutUpRight, Podium } from "lucide-react";
import ProgressBar from "../General/ProgressBar";
import type { Tier, UserRating } from "../../util/NetworkModels";
import { calculateDivision, determineTier, divisionProgress, toRoman, winRate } from "../../util/helpers";
import { returnIcon } from "../../util/rankedIconPicker";

interface QueueCardProps {
    rating: UserRating;
    tiers: Tier[]
}

export default function QueueCard(props: QueueCardProps) {
    const { user, loading } = useAuth();

    const tierIndex = determineTier(props.tiers, props.rating.display_rating)
    const division: number | null = calculateDivision(props.tiers, props.rating.display_rating, tierIndex);
    const progress = divisionProgress(props.tiers, props.rating.display_rating, tierIndex);

    return loading ? (
        <></>
    ) : (
        <>
            <div className="w-1/4 bg-background-dark p-5 rounded-md flex flex-col">
                <p className="text-center font-bold text-2xl mb-5">
                    {props.rating.ladder == "ec" ? "BMS Easy Clear Ladder" : "BMS Hard Clear Ladder"}
                </p>

                <div className="flex flex-row justify-center items-center">
                    <div className="flex-1 flex items-center h-ful flex-col gap-4">
                        <div>
                            <img className="w-32" src={returnIcon(props.tiers[tierIndex].name)}/>
                        </div>
                        <div className="items-center font-bold text-xl tracking-wide">
                            {props.tiers[tierIndex].name} {toRoman(division ?? 1)}
                        </div>

                        <div className="w-40">
                            <ProgressBar
                            value={progress?.percent ?? 0}
                            className="bg-highlight" 
                            />
                        <div className="flex flex-row justify-between text-subtext mt-2">
                            <p>{progress?.start}</p>
                            <p>{progress?.end}</p>
                        </div>
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col gap-4 justify-center h-full items-center">
                        <div className="text-center flex flex-col gap-1">
                            <p className="text-xs uppercase tracking-widest text-subtext">Rating</p>
                            <p className="text-3xl font-bold tabular-nums">{props.rating.display_rating.toFixed(0)}</p>
                            <p className="text-xs text-subtext">#{props.rating.rank} of {props.rating.total}</p>
                        </div>
                        <div className="text-center flex flex-col gap-1">
                            <p className="text-xs uppercase tracking-widest text-subtext">Record</p>
                            <p className="text-xl font-bold tabular-nums">
                            <span className="text-green-600">{props.rating.wins}W</span> · <span className="text-red-600">{props.rating.losses}L</span>
                            </p>
                            <p className="text-xs text-subtext">{winRate(props.rating.wins, props.rating.losses)?.toFixed(2)}% win rate</p>
                        </div>
                    </div>
                </div>

            <div className="flex flex-row justify-end gap-5 mt-5">
                <div className="">
                    <Button className="inline-flex items-center gap-2 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Queue Casual <CircleArrowOutUpRight className="size-4"/></Button>
                </div>

                <div className="text-right">
                    <Button className="inline-flex items-center gap-2 bg-highlight brightness-80 hover:brightness-100 duration-200 cursor-pointer p-3 rounded-sm font-semibold">Queue Ranked <Podium className="size-4"/></Button>
                </div>
            </div>

            </div>
        </>
    )
}