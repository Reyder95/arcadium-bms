import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../util/helpers";

type User = { id: number; username: string; display_name: string; avatar_url: string | null};

type AuthState = {
    user: User | null;
    loading: boolean;
    refresh: () => Promise<void>;
    logout: () => Promise<void>;
    login: (identifier: string, password: string) => Promise<void>;
    register: (username: string, email: string, display_name: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    async function refresh() {
        return api<User>("/auth/me")
        .then(me => {
            setUser(me)
        }).catch(() => {
            setUser(null)
        }).finally(() => {
            setLoading(false)
        })
    }

    async function logout() {
        return api<void>("/auth/logout", { method: "POST" }).finally(() => setUser(null))
    }

    useEffect(() => {
        refresh();
    }, [])

    async function login(identifier: string, password: string) {
        const me = await api<User>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ identifier, password })
        });
        setUser(me);
    }

    async function register(username: string, email: string, display_name: string, password: string) {
        const me = await api<User>("/auth/register", {
            method: "POST",
            body: JSON.stringify({ username, email, display_name, password})
        });
        setUser(me);
    }

    return (
        <AuthContext.Provider value={{ user, loading, refresh, logout, login, register}}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
}