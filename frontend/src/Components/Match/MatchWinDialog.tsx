import { Dialog, DialogBackdrop, DialogPanel, DialogTitle, Button } from "@headlessui/react";
import { Trophy, X } from "lucide-react";

type MatchWinDialogProps = {
  open: boolean;
  win: boolean;
  onClose: () => void;
  ratingChange?: number;
};

export function MatchWinDialog({ open, win, onClose, ratingChange }: MatchWinDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <DialogBackdrop
        transition
        className="fixed inset-0 bg-black/60 transition duration-200 data-closed:opacity-0"
      />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel
          transition
          className="w-full max-w-sm rounded-lg bg-foreground p-8 text-center
                     transition duration-200 ease-out data-closed:opacity-0 data-closed:scale-95"
        >
          {
            win ? <Trophy className="mx-auto size-12 text-highlight" /> : <X className="mx-auto size-12 text-highlight"/>
          }
          

          <DialogTitle className="mt-4 font-archivo text-3xl uppercase tracking-widest">
            {
              win ? "Match win!" : "Match lose!"
            }
          </DialogTitle>

          {ratingChange !== undefined && (
            <p className="mt-2 text-xl font-bold text-green-500 tabular-nums">
              +{Math.round(ratingChange)}
            </p>
          )}

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