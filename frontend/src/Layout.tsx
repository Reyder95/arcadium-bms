import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Link, Outlet, useLocation, useMatch } from "react-router";
import UserButton from "./Components/Navigation/UserButton";

import arcadiumTextLogo from './assets/Arcadium Logo Text.png';
import arcadiumIconLogo from './assets/Arcadium Logo Icon.png';
import { useAuth } from "./hooks/useAuth";
import { useEffect, useState } from "react";
import { type Match } from "./util/NetworkModels";
import { api } from "./util/helpers";

export default function Layout() {

    const {user, loading} = useAuth();
    const onMatchPage = useMatch("/match/:id");

    const [activeMatch, setActiveMatch] = useState<Match | null>();

    useEffect(() => {
        api<Match | null>("/users/me/active-match")
        .then(match => {
            setActiveMatch(match)
        })
    }, [user])

    return (
        <div className="min-h-dvh flex flex-col">
            <nav className="font-sanchez min-h-d bg-background-dark flex flex-row gap-20 font-bold tracking-wider p-7 border-b border-highlight items-center">
                <Link to="/" className="mr-auto flex flex-row items-center gap-2">
                        <img src={arcadiumIconLogo} alt="Arcadium Icon" className="h-18"/>
                        <img src={arcadiumTextLogo} alt="Arcadium Text" className="h-20" />
                </Link>

                {activeMatch ? (
                    !onMatchPage && (
                        <Link
                        to={`/match/${activeMatch.id}`}
                        className="flex items-center gap-2 text-red-600 hover:text-red-400 transition-colors duration-150"
                        >
                            Return to Active Match
                        </Link>
                    )
                    ) : (
                        <Menu>
                            <MenuButton className="focus:outline-none flex items-center gap-2 hover:text-highlight transition-colors duration-150">
                            Queue <ChevronDown className="size-6 scale-x-90" />
                            </MenuButton>
                            <MenuItems
                            anchor={{ to: "bottom start", gap: 30}}
                            transition
                            className="focus:outline-none flex flex-col gap-6 bg-foreground p-5 rounded-md font-bold transition duration-150 ease-out data-closed:opacity-0 w-50"
                            >
                                <div className="px-1 text-xs uppercase tracking-widest text-muted">BMS</div>
                                <MenuItem>
                                    <Link to="/prep/bms/7k/ec" className="block data-focus:text-highlight duration-150">7K Easy Clear</Link>
                                </MenuItem>
                                <MenuItem>
                                    <Link to="/prep/bms/7k/hc" className="block data-focus:text-highlight durationg-150">7K Hard Clear</Link>
                                </MenuItem>
                            </MenuItems>
                        </Menu>
                    )
                    }


                <Menu>
                    <MenuButton className="focus:outline-none flex items-center gap-2 hover:text-highlight transition-colors duration-150">
                        Rankings <ChevronDown className="size-6 scale-x-90" />   
                    </MenuButton>

                    <MenuItems
                    anchor={{ to: "bottom start", gap: 30}}
                    transition
                    className="focus:outline-none flex flex-col gap-6 bg-foreground p-5 rounded-md font-bold transition duration-150 ease-out data-closed:opacity-0 w-50"
                    >
                        <MenuItem>
                            <Link className="hover:text-highlight duration-150" to="/">Players</Link>
                        </MenuItem>
                        <MenuItem>
                            <Link className="hover:text-highlight duration-150" to="/">Charts</Link>
                        </MenuItem>
                    </MenuItems>
                </Menu>

                <Link className="hover:text-highlight duration-150" to="/">Tier Guide</Link>
                <Link className="hover:text-highlight duration-150" to="/">Quick Setup</Link>
                <Link className="hover:text-highlight duration-150" to="/">FAQ</Link>

                <div>
                    <UserButton />
                </div>
            </nav>
            <main className="flex-1 flex flex-col">
                <Outlet />
            </main>
        </div>
    )
}