// src/app/page.tsx

"use client";

import { useState, FormEvent, useEffect } from "react";
import { motion } from "framer-motion";
import styles from "./page.module.css";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], weight: ["600"] });

type Message = { role: "user" | "assistant"; content: string };

enum Role {
    USER = "user",
    ASSISTANT = "assistant",
}

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [latency, setLatency] = useState<number | null>(null);

    const [showLogin, setShowLogin] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [token, setToken] = useState<string | null>(null);

    const modelOptions = [
        { value: "gpt2_native", label: "GPT-2 (native PyTorch)" },
        { value: "gpt2_onnx", label: "GPT-2 (Open Neural Network Exchange)" },
        { value: "Llama2.7", label: "Llama2.7" },
        { value: "BonQuiQui", label: "Llama2.7 Bon Qui Qui" },
        { value: "MsSwan", label: "Llama2.7 Ms Swan" },
        { value: "Bonifa", label: "Llama2.7 Bonifa" },
    ];

    const [selectedModel, setSelectedModel] = useState(modelOptions[0].value);

    // Reset chat and latency when model changes
    useEffect(() => {
        setMessages([]);
        setLatency(null);
    }, [selectedModel]);

    // Load token from localStorage
    useEffect(() => {
        const saved = localStorage.getItem("token");
        if (saved) setToken(saved);
    }, []);

    const handleLogin = async (e: FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            if (!res.ok) throw new Error("Login failed");
            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            setToken(data.access_token);
            setShowLogin(false);
        } catch {
            alert("Login failed. Check credentials.");
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        const content = input.trim();
        if (!content) return;

        // Build new messages state
        const userMsg: Message = { role: Role.USER, content };
        const newMessages = [...messages, userMsg];
        setMessages(newMessages);
        setInput("");
        setLoading(true);

        // Prepare payload messages
        let payloadMessages: Message[];
        if (selectedModel.startsWith("gpt2")) {
            // Stateless GPT-2: send only the latest user message
            payloadMessages = [userMsg];
        } else {
            // Stateful LLaMA: include history + persona (once) + new message
            payloadMessages = [...newMessages];
            if (messages.length === 0) {
                // Inject persona prompt only on first turn
                if (selectedModel === "BonQuiQui") {
                    payloadMessages.unshift({
                        role: Role.USER,
                        content: "You are Bon Qui Qui, a comically rude, gangsta cashier. Always say 'I WILL CUUUUT you!' and 'Seccurrrity! You need to go!'. Respond with humor, sarcasm, and attitude."
                    });
                } else if (selectedModel === "MsSwan") {
                    payloadMessages.unshift({
                        role: Role.USER,
                        content: "You are Ms. Swan, a quirky, heavily-accented woman known for her catchphrase 'He look-a like a man.' Respond evasively and exasperatingly."
                    });
                } else if (selectedModel === "Bonifa") {
                    payloadMessages.unshift({
                        role: Role.USER,
                        content: "You are Bonifa Latifa Halifa Sherifa Jackson, loud, brash, and constantly yakking on her cell. Demand respect with humor and sass."
                    });
                }
            }
        }

        // Determine endpoint
        const endpoint =
            selectedModel === "gpt2_native" ? "/chat/native-gpt2"
                : selectedModel === "gpt2_onnx" ? "/chat/onnx-gpt2"
                    : "/chat/stream";

        const start = performance.now();
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers.Authorization = `Bearer ${token}`;

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}${endpoint}`,
                {
                    method: "POST",
                    headers,
                    body: JSON.stringify({
                        model: selectedModel.startsWith("gpt2") ? "gpt2" : selectedModel,
                        messages: payloadMessages,
                    }),
                }
            );
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            if (endpoint === "/chat/stream") {
                // Streaming LLaMA
                setMessages(prev => [...prev, { role: Role.ASSISTANT, content: "" }]);
                const reader = res.body!.getReader();
                const decoder = new TextDecoder();
                let done = false;
                while (!done) {
                    const { value, done: d } = await reader.read();
                    done = d;
                    if (value) {
                        const chunk = decoder.decode(value);
                        setMessages(prev => {
                            const msgs = [...prev];
                            const lastIndex = msgs.length - 1;
                            let prevText = msgs[lastIndex].content;
                            // Deduplicate overlapping prefix
                            let overlap = 0;
                            const maxOverlap = Math.min(prevText.length, chunk.length);
                            for (let i = maxOverlap; i > 0; i--) {
                                if (prevText.endsWith(chunk.substring(0, i))) {
                                    overlap = i;
                                    break;
                                }
                            }
                            const toAdd = chunk.substring(overlap);
                            msgs[lastIndex].content = prevText + toAdd;
                            return msgs;
                        });
                    }
                }
            } else {
                // JSON GPT-2
                const { reply } = await res.json();
                setMessages(prev => [...prev, { role: Role.ASSISTANT, content: reply }]);
            }

            setLatency(performance.now() - start);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`${styles.page} ${inter.className}`}>
            <header className={styles.header}>
                <div className={styles.logoSection}>
                    <span role="img" aria-label="moon" className={styles.logoEmoji}>🌙</span>
                    <h1 className={styles.title}>NEPTUNE AI</h1>
                    <select
                        className={styles.modelSelect}
                        value={selectedModel}
                        onChange={e => setSelectedModel(e.target.value)}
                    >
                        {modelOptions.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                </div>
                <div className={styles.profileSection}>
                    <span role="img" aria-label="profile" className={styles.profileEmoji} onClick={() => setShowLogin(true)}>😊</span>
                </div>
            </header>

            <main className={styles.chatContainer}>
                <div className={styles.chatArea}>
                    {messages.map((m, i) => {
                        let text = m.content;
                        if (m.role === Role.ASSISTANT && !selectedModel.startsWith("gpt2")) {
                            const label = selectedModel === "BonQuiQui" ? "Bon Qui Qui"
                                : selectedModel === "MsSwan" ? "Ms Swan"
                                    : selectedModel === "Bonifa" ? "Bonifa"
                                        : "Assistant";
                            text = `${label}: ${m.content}`;
                        }
                        return (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: i * 0.1 }}
                                className={m.role === Role.USER ? styles.userMessage : styles.assistantMessage}
                            >
                                {text}
                            </motion.div>
                        );
                    })}
                </div>

                {latency != null && <p className={styles.latency}>Response time: {latency.toFixed(1)} ms</p>}
                {loading && <p className={styles.loading}>Assistant is typing…</p>}

                <form onSubmit={handleSubmit} className={styles.inputArea}>
                    <input
                        className={styles.inputField}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="Type a message…"
                    />
                    <button type="submit" className={styles.sendButton}>Send</button>
                </form>
            </main>

            {showLogin && (
                <div className={styles.modalBackdrop}>
                    <div className={styles.modal}>
                        <h2>Login</h2>
                        <form onSubmit={handleLogin} className={styles.modalForm}>
                            <input className={styles.modalInput} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
                            <input className={styles.modalInput} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
                            <button type="submit" className={styles.modalButton}>Log In</button>
                        </form>
                        <button onClick={() => setShowLogin(false)} className={styles.modalClose}>Cancel</button>
                    </div>
                </div>
            )}
        </div>
    );
}
