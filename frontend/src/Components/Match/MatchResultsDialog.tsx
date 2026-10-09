import { Dialog, DialogBackdrop, DialogPanel, DialogTitle, Button } from "@headlessui/react";
import { Trophy, X } from "lucide-react";
import type { Tier } from "../../util/NetworkModels";
import { QueueIcon } from "../Home/QueueCard";
import ProgressBar from "../General/ProgressBar";
import { buildSteps, divisionProgress, nextTierInfo, returnBeginningAndEndRating, toFixedTruncated, toRoman } from "../../util/helpers";
import type { BetweenTierData } from "../../util/MiscInterfaces";
import { useEffect, useMemo, useState } from "react";

type MatchResultDialogProps = {
  open: boolean;
  win: boolean;
  onClose: () => void;
  ratingChange?: number;

  tierIndex: number | null;
  division: number | null;
  tiers: Tier[];
  rating_before: number;
  rating_after: number;
};

export function MatchResultsDialog({ open, win, onClose, ratingChange, tierIndex, division, tiers, rating_before, rating_after }: MatchResultDialogProps) {

  const begAndEndRating : BetweenTierData = returnBeginningAndEndRating(rating_before ?? 0, rating_after ?? 0, tiers)
  const steps = useMemo(
    () => buildSteps(rating_before ?? 0, rating_after ?? 0, tiers),
    [rating_before, rating_after, tiers]
  );

  const next = useMemo(
  () => nextTierInfo(rating_after, steps[steps.length - 1], tiers),
  [rating_after, steps, tiers]
  );

  const nextTier = next.nextTierIndex != null ? tiers[next.nextTierIndex] : null;
  const lastStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const range = lastStep ? divisionProgress(tiers, rating_after, lastStep.tierIndex) : null;

  console.log(steps);

  const [i, setI] = useState(0);
  const [currProgress, setCurrProgress] = useState(steps[0].from)
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    if (!open) return

    setAnimate(false);
    setCurrProgress(steps[i].from);

    const id = setTimeout(() => {
      setAnimate(true)
      setCurrProgress(steps[i].to)
    }, 50)
    return () => clearTimeout(id);
  }, [i, open])

  useEffect(() => {
    if (currProgress == 100)
      console.log("SWAP RATINGS")
  }, [currProgress])

  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <DialogBackdrop
        transition
        className="fixed inset-0 bg-black/60 transition duration-200 data-closed:opacity-0"
      />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel
          transition
          className="w-full max-w-2xl rounded-lg bg-foreground p-8 text-center
                     transition duration-200 ease-out data-closed:opacity-0 data-closed:scale-95"
        >
          <p className="text-left font-archivo tracking-[0.2em] text-subtext text-xl">MATCH RESULTS</p>
          

          <DialogTitle className="mt-4 font-archivo text-3xl uppercase tracking-widest">
            {
              win ? (<span className="text-green-800">CLEAR</span>) : <span className="text-red-800">FAIL</span>
            }
          </DialogTitle>

          <QueueIcon
            tierIndex={steps[i].tierIndex}
            division={steps[i].divisionNumber}
            tiers={tiers}
            rating={rating_after}
            displayRating={true}
            displayProgress={false}
          />

          <div className="w-3/4 mx-auto mt-5">
            <ProgressBar
            durationMs={Math.abs(steps[i].to - steps[i].from) * 100}
            value={currProgress}
            animate={animate}
            onTransitionEnd={() => {
              if (i < steps.length - 1) setI(i + 1);
            }}
            />
                    <div className="font-sanchez flex flex-row justify-between text-subtext mt-2 text-sm">
                      <p>{range?.start ?? 0}</p>
                      <p>
                        {nextTier?.name} {next.nextDivision !== null ? toRoman(next.nextDivision) : "V"} &middot; {range?.end ?? 0}
                      </p>
                    </div> 
          </div>

          <p className="font-archivo text-2xl mt-5">
            <span className={`${rating_after >= rating_before ? "text=green-800" : "text-red-800"} bg-background px-4 py-2 rounded-md`}>{rating_after > rating_before ? "+" : ""}{toFixedTruncated((rating_after - rating_before), 0)}</span>
          </p>

          <Button
            onClick={onClose}
            className="mt-6 w-full h-10 rounded-md bg-highlight font-semibold
                       data-hover:brightness-110 transition cursor-pointer"
          >
            Continue
          </Button>
        </DialogPanel>
      </div>
    </Dialog>
  );
}