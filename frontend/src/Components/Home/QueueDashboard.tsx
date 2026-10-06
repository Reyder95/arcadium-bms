import { useAuth } from "../../hooks/useAuth";
import QueueCard from "./QueueCard";

export default function QueueDashboard() {

    const { user, loading } = useAuth();

    return loading ? (
        <></> ) : (
        <>
            <div className="flex items-center gap-5 justify-center w-full bg-foreground p-5">
                <QueueCard />
                <QueueCard />
            </div>
        </>
    )

}