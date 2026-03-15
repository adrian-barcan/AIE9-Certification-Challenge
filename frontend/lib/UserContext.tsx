"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister, User } from "@/lib/api";

interface UserContextType {
    user: User | null;
    loading: boolean;
    register: (name: string, email: string, password: string, preferred_language: string, risk_tolerance: string) => Promise<void>;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const UserContext = createContext<UserContextType>({
    user: null,
    loading: true,
    register: async () => { },
    login: async () => { },
    logout: () => { },
});

export function useUser() {
    return useContext(UserContext);
}

export function UserProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const controller = new AbortController();
        const timeoutMs = 8000;
        const timeoutId = window.setTimeout(() => {
            controller.abort();
        }, timeoutMs);
        let isMounted = true;

        getMe(controller.signal)
            .then((me) => {
                if (!isMounted) return;
                setUser(me);
            })
            .catch(() => {
                if (!isMounted) return;
                setUser(null);
            })
            .finally(() => {
                window.clearTimeout(timeoutId);
                if (!isMounted) return;
                setLoading(false);
            });

        return () => {
            isMounted = false;
            window.clearTimeout(timeoutId);
            controller.abort();
        };
    }, []);

    const register = async (
        name: string,
        email: string,
        password: string,
        preferred_language: string,
        risk_tolerance: string
    ) => {
        const newUser = await apiRegister(name, email, password, preferred_language, risk_tolerance);
        setUser(newUser);
    };

    const login = async (email: string, password: string) => {
        const loggedInUser = await apiLogin(email, password);
        setUser(loggedInUser);
    };

    const logout = () => {
        apiLogout().catch(() => {
            // Ensure local state is cleared even if backend session is already invalid.
        }).finally(() => {
            setUser(null);
        });
    };

    return (
        <UserContext.Provider value={{ user, loading, register, login, logout }}>
            {children}
        </UserContext.Provider>
    );
}
