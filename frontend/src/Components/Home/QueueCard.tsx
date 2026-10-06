import { useAuth } from "../../hooks/useAuth";

import rankedIcon from "../../assets/ranked_icons/Diamond-cropped.png";
import { Button } from "@headlessui/react";
import { CircleArrowOutUpRight, Podium } from "lucide-react";
import ProgressBar from "../General/ProgressBar";
import type { UserRating } from "../../util/NetworkModels";

interface QueueCardProps {
    rating: UserRating
}

export default function QueueCard(props: QueueCardProps) {
    const { user, loading } = useAuth();

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
                            <img className="w-32" src={rankedIcon}/>
                        </div>
                        <div className="items-center font-bold text-xl tracking-wide">
                            Diamond III
                        </div>

                        <div className="w-40">
                            <ProgressBar
                            value={75}
                            className="bg-highlight" 
                            />
                        <div className="flex flex-row justify-between text-subtext mt-2">
                            <p>3100</p>
                            <p>3200</p>
                        </div>
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col gap-4 justify-center h-full items-center">
                        <div className="text-center flex flex-col gap-1">
                            <p className="text-xs uppercase tracking-widest text-subtext">Rating</p>
                            <p className="text-3xl font-bold tabular-nums">3190</p>
                            <p className="text-xs text-subtext">#155 of 1,278</p>
                        </div>
                        <div className="text-center flex flex-col gap-1">
                            <p className="text-xs uppercase tracking-widest text-subtext">Record</p>
                            <p className="text-xl font-bold tabular-nums">
                            <span className="text-green-600">25W</span> · <span className="text-red-600">15L</span>
                            </p>
                            <p className="text-xs text-subtext">62.5% win rate</p>
                        </div>
                    </div>
                </div>

            <div className="flex flex-row justify-end gap-5 mt-5">
                <div className="">
                    <Button className="inline-flex items-center gap-2 bg-green-800 hover:bg-green-600 duration-200 cursor-pointer p-2 rounded-sm font-bold">Queue Casual <CircleArrowOutUpRight className="size-4"/></Button>
                </div>

                <div className="text-right">
                    <Button className="inline-flex items-center gap-2 bg-green-800 hover:bg-green-600 duration-200 cursor-pointer p-2 rounded-sm font-bold">Queue Ranked <Podium className="size-4"/></Button>
                </div>
            </div>

            </div>
        </>
    )
}