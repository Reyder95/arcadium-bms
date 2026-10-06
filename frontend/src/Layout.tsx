import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { ChevronDown } from "lucide-react";
import { Link, Outlet } from "react-router";
import UserButton from "./Components/Navigation/UserButton";

import arcadiumTextLogo from './assets/Arcadium Logo Text.png';
import arcadiumIconLogo from './assets/Arcadium Logo Icon.png';
import { useAuth } from "./hooks/useAuth";

export default function Layout() {

    return (
        <>
            <nav className="font-sanchez bg-background-dark flex flex-row gap-20 font-bold tracking-wider p-7 border-b border-highlight items-center">
                <div className="mr-auto flex flex-row items-center gap-2" >
                    <img src={arcadiumIconLogo} alt="Arcadium Icon" className="h-18"/>
                    <img src={arcadiumTextLogo} alt="Arcadium Text" className="h-20" />
                </div>
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
            <main>
                <Outlet />
            </main>
        </>
    )
}