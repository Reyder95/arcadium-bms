import { useState } from "react";

type ProfileImageProps = {
    username: string;
    src?: string | null;
    className?: string;
}

export default function ProfileImage({ username, src, className = "size-10"}: ProfileImageProps) {
    const [failed, setFailed] = useState(false);

    const fallback = `https://api.dicebear.com/9.x/identicon/svg?seed=${encodeURIComponent(username)}`;
    const imageUrl = src && !failed ? src : fallback;

    return (
        <img
        src={imageUrl}
        alt={`${username}'s avatar`}
        onError={() => setFailed(true)}
        className={`rounded-lg object-cover bg-surface border border-border ${className}`}
        />
    );
}