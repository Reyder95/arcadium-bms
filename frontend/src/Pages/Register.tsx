import { Button, Field, Fieldset, Input, Label, Legend } from "@headlessui/react";
import { Link, useLocation, useNavigate } from "react-router";
import { useAuth } from "../hooks/useAuth";
import { useState } from "react";

export default function Register() {

    const { register } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    
    const [username, setUsername] = useState<string>();
    const [displayName, setDisplayName] = useState<string>();
    const [email, setEmail] = useState<string>();
    const [emailConfirm, setEmailConfirm] = useState<string>();
    const [password, setPassword] = useState<string>();
    const [passwordConfirm, setPasswordConfirm] = useState<string>();
    const [inviteCode, setInviteCode] = useState<string>();

    const [error, setError] = useState<string | null>(null)

    const handleRegister = async () => {
        if (
            !username ||
            !email ||
            !emailConfirm ||
            !password ||
            !passwordConfirm
        ) 
        return;

        if (
            username.trim() == "" ||
            email.trim() == "" ||
            emailConfirm.trim() == "" ||
            password.trim() == "" ||
            passwordConfirm.trim() == ""
        )
        return

        if (
            (email != emailConfirm) ||
            (password != passwordConfirm)
        )
        return

        try {
            await register(String(username), String(email), String(displayName), String(password));
            navigate(location.state?.from?.pathname ?? "/", { replace: true });
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center">
            <form className="w-1/4">
                <Fieldset className="space-y-8">
                    <Legend className="text-4xl font-bold">Register</Legend>

                    <Field>
                        <Label className="block font-bold">Username</Label>
                        <Input 
                        onInput={(e) => setUsername(e.currentTarget.value)} 
                        value={username} 
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md font-semibold focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="username"
                        />
                    </Field>

                    <Field>
                        <Label className="block font-bold">Display name</Label>
                        <Input 
                        onInput={(e) => setDisplayName(e.currentTarget.value)} 
                        value={displayName}
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md font-semibold focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="username"
                        />
                    </Field>

                    <Field>
                        <Label className="block font-bold">Email</Label>
                        <Input 
                        onInput={(e) => setEmail(e.currentTarget.value)}
                        value={email}
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md font-semibold focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="email"
                        />
                    </Field>

                    <Field>
                        <Label className="block font-bold">Confirm Email</Label>
                        <Input
                        onInput={(e) => setEmailConfirm(e.currentTarget.value)}
                        value={emailConfirm} 
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md font-semibold focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="emailConfirm"/>
                    </Field>

                    <Field>
                        <Label className="block font-bold">Password</Label>
                        <Input
                        onInput={(e) => setPassword(e.currentTarget.value)}
                        value={password} 
                        type="password" 
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="password"/>
                    </Field>

                    <Field>
                        <Label className="block font-bold">Confirm Password</Label>
                        <Input
                        onInput={(e) => setPasswordConfirm(e.currentTarget.value)}
                        value={passwordConfirm} 
                        type="password" 
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="passwordConfirm"/>
                    </Field>

                    <Field>
                        <Label className="block font-bold">Invite Code</Label>
                        <Input 
                        onInput={(e) => setInviteCode(e.currentTarget.value)}
                        value={inviteCode}
                        type="password" 
                        className="mt-1 block bg-background-dark w-full p-2 rounded-md focus:outline-none data-hover:bg-zinc-600/25 duration-200" 
                        name="inviteCode"/>
                    </Field>

                    <Field className="flex justify-end gap-5 items-center">
                        <div>
                            <p>Already have an account? <Link className="text-highlight hover:text-purple-400 duration-200" to="/login">Log in!</Link></p>
                        </div>
                        <Button type="submit" onClick={(e) => { e.preventDefault(); handleRegister() }} className="bg-zinc-600 p-4 rounded-md hover:bg-zinc-500 duration-200 cursor-pointer w-1/6 font-bold">Register</Button>
                    </Field>
                </Fieldset>
            </form>


        </div>
    )
}