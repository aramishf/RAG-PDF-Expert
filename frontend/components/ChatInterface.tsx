import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, Bot, Plus, ArrowUp, Square, FileText } from 'lucide-react';
import MagneticButton from './ui/MagneticButton';
import LogoAF from './ui/LogoAF';
import { sendChat, uploadFiles, type ChatMessage } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

export default function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
    const [uploadedFiles, setUploadedFiles] = useState<Set<string>>(new Set());
    const [hasStartedChatting, setHasStartedChatting] = useState(false);

    const abortControllerRef = useRef<AbortController | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        // STOP LOGIC
        if (isLoading) {
            abortControllerRef.current?.abort();
            abortControllerRef.current = null;
            setIsLoading(false);

            // Remove "Thinking..." if it's the last message
            setMessages(prev => {
                if (prev.length > 0 && prev[prev.length - 1].content === 'Thinking...') {
                    return prev.slice(0, -1);
                }
                return prev;
            });
            return;
        }

        if (!input.trim()) return;

        // SEND LOGIC
        const question = input;
        setInput('');
        setIsLoading(true);
        setHasStartedChatting(true);

        setMessages(prev => [...prev, { role: 'user', content: question }]);
        setMessages(prev => [...prev, { role: 'assistant', content: 'Thinking...' }]);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        try {
            const response = await sendChat(question, abortController.signal);

            setMessages(prev => {
                const withoutThinking = prev.slice(0, -1);
                return [...withoutThinking, {
                    role: 'assistant',
                    content: response.answer,
                    citations: response.citations
                }];
            });
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                console.log('Request aborted by user');
                return;
            }

            setMessages(prev => {
                const withoutThinking = prev.slice(0, -1);
                return [...withoutThinking, {
                    role: 'assistant',
                    content: `⚠️ **Error**: ${error instanceof Error ? error.message : "Unknown error occurred"}`
                }];
            });
        } finally {
            if (abortControllerRef.current === abortController) {
                setIsLoading(false);
                abortControllerRef.current = null;
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleUploadClick = () => fileInputRef.current?.click();

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const files = Array.from(e.target.files);
            const newFiles = files.filter(f => !uploadedFiles.has(f.name));

            if (newFiles.length === 0) {
                alert('All selected files have already been uploaded.');
                return;
            }
            if (newFiles.length < files.length) {
                const skipped = files.length - newFiles.length;
                alert(`Skipped ${skipped} duplicate file(s).`);
            }

            setUploadingFiles(newFiles);
            setIsUploading(true);

            try {
                await uploadFiles(newFiles);
                setUploadedFiles(prev => new Set([...prev, ...newFiles.map(f => f.name)]));
                // Do NOT add message here. State update is enough for chips.
            } catch (error) {
                console.error('Upload error:', error);
                const errorMessage = error instanceof Error ? error.message : 'Upload failed';
                alert(`Upload Failed: ${errorMessage}`);
            } finally {
                setIsUploading(false);
                setUploadingFiles([]);
                if (fileInputRef.current) fileInputRef.current.value = '';
            }
        }
    };



    return (
        <div className="flex flex-col h-screen text-white bg-[#0A0A0A] font-sans selection:bg-[#D4AF37] selection:text-black">
            {/* Background Effects */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#D4AF37]/5 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#D4AF37]/5 rounded-full blur-[120px]" />
            </div>

            {/* Header */}
            <header className={cn(
                "fixed top-0 left-0 w-full p-6 flex items-center justify-between z-50 transition-all duration-500",
                hasStartedChatting ? "bg-[#0A0A0A]/80 backdrop-blur-md border-b border-white/5" : "bg-transparent"
            )}>
                <div className="flex items-center gap-3">
                    <LogoAF className={cn("transition-all duration-500", hasStartedChatting ? "w-8 h-8" : "w-12 h-12")} />
                    <span className={cn(
                        "font-bold tracking-wider text-[#D4AF37] transition-all duration-500",
                        hasStartedChatting ? "text-lg" : "text-xl"
                    )}>
                        AI RESEARCH ASSISTANT
                    </span>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 relative flex flex-col w-full max-w-5xl mx-auto z-10 pt-24 overflow-hidden">

                {/* Intro / Welcome State */}
                {!hasStartedChatting && (
                    <div className="flex-1 flex flex-col items-center justify-start pt-[15vh]">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-center space-y-6 mb-12"
                        >
                            <div className="relative inline-block">
                                <div className="absolute inset-0 bg-transparent" />
                                <img
                                    src="/ai_avatar.png"
                                    alt="AI Assistant"
                                    className="w-40 h-40 relative z-10 drop-shadow-2xl object-cover rounded-2xl mx-auto"
                                />
                            </div>
                            <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#D4AF37] via-[#F3E5AB] to-[#D4AF37]">
                                What would you like to know?
                            </h1>
                            <p className="text-white/40 text-lg max-w-xl mx-auto">
                                Upload your documents and ask complex questions. I'll analyze them for you.
                            </p>
                        </motion.div>
                    </div>
                )}

                {/* Messages List */}
                {hasStartedChatting && (
                    <div className="flex-1 overflow-y-auto px-4 space-y-8 scroll-smooth pb-60" ref={scrollRef}>
                        <AnimatePresence initial={false}>
                            {messages.map((msg, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn("flex gap-6 mb-12 max-w-4xl mx-auto", msg.role === 'user' ? "flex-row-reverse" : "")}
                                >
                                    <div className={cn(
                                        "w-10 h-10 flex items-center justify-center flex-shrink-0 rounded-full overflow-hidden",
                                        msg.role !== 'user' ? "bg-transparent" : "w-8 h-8 rounded-lg bg-black/40 border-black/50 text-white text-xs font-bold"
                                    )}>
                                        {msg.role !== 'user' ? (
                                            <img src="/bot-avatar.png?v=2" alt="AI Agent" className="w-full h-full object-cover" />
                                        ) : (
                                            "AF"
                                        )}
                                    </div>

                                    <div className={cn("max-w-[85%]", msg.role === 'user' ? "text-right" : "")}>
                                        <div className={cn(
                                            "inline-block rounded-2xl px-6 py-4 shadow-xl backdrop-blur-sm border",
                                            msg.role === 'user'
                                                ? "bg-[#D4AF37] text-black font-medium border-[#F3E5AB]/20"
                                                : "bg-[#1A1A1A]/80 text-white/90 border-white/5"
                                        )}>
                                            {msg.content === 'Thinking...' ? (
                                                <div className="flex items-center gap-3">
                                                    <span className="animate-pulse">Thinking...</span>
                                                </div>
                                            ) : (
                                                <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 text-left">
                                                    <ReactMarkdown components={{
                                                        // Override strong/bold to utilize gold color for emphasis
                                                        strong: ({ node, ...props }: any) => <span className="font-bold text-[#D4AF37]" {...props} />,
                                                        a: ({ node, ...props }: any) => <a className="text-[#F3E5AB] underline hover:text-[#D4AF37] transition-colors" {...props} />
                                                    }}>
                                                        {msg.content}
                                                    </ReactMarkdown>

                                                    {msg.citations && msg.citations.length > 0 && (
                                                        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/10 not-prose">
                                                            {msg.citations
                                                                .filter((cite, index, self) =>
                                                                    index === self.findIndex((t) => (
                                                                        t.source === cite.source && t.page === cite.page
                                                                    ))
                                                                )
                                                                .map((cite, i) => {
                                                                    const bookName = cite.source?.replace('.pdf', '') || 'Unknown';
                                                                    const abbreviation = bookName.split('-').map(w => w[0]?.toUpperCase()).join('');
                                                                    return (
                                                                        <span key={i} className="text-xs bg-white/10 text-[#D4AF37] px-2 py-1 rounded cursor-help" title={`${cite.source} (p.${cite.page})`}>
                                                                            [{abbreviation} p.{cite.page}]
                                                                        </span>
                                                                    );
                                                                })}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}

                {/* Movable Input Area */}
                <div className={cn(
                    "fixed left-0 w-full px-4 z-40 transition-all duration-700 ease-in-out",
                    hasStartedChatting ? "bottom-8" : "bottom-[35%] translate-y-1/2"
                )}>
                    <div className="max-w-3xl mx-auto space-y-4">
                        {/* Chips for files */}
                        {(uploadedFiles.size > 0 || uploadingFiles.length > 0) && (
                            <div className="flex flex-wrap gap-2 justify-center mb-2">
                                {uploadingFiles.map((f, i) => (
                                    <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-[#1A1A1A]/80 border border-white/10 rounded-full text-xs text-white/70 animate-pulse">
                                        <Sparkles className="w-3 h-3 text-[#D4AF37]" />
                                        <span>Uploading {f.name}...</span>
                                    </div>
                                ))}
                                {Array.from(uploadedFiles).map(file => (
                                    <div key={file} className="flex items-center gap-2 px-3 py-1.5 bg-[#1A1A1A] border border-white/10 rounded-full text-xs text-white/70">
                                        <FileText className="w-3 h-3 text-[#D4AF37]" />
                                        <span>{file}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Input Container */}
                        <div className="bg-gradient-to-r from-[#e3c788] via-[#d4af37] to-[#aa8c2c] rounded-3xl p-2 pl-6 flex items-end gap-4 shadow-2xl shadow-[#D4AF37]/20 border border-[#F3E5AB]/40 ring-1 ring-[#D4AF37]/20 focus-within:ring-[#F3E5AB]/50 transition-all duration-300">
                            <input type="file" multiple accept=".pdf" className="hidden" ref={fileInputRef} onChange={handleFileChange} />

                            <textarea
                                className="flex-1 bg-transparent border-0 focus:ring-0 resize-none max-h-40 min-h-[48px] py-3 text-base text-[#1A1A1A] placeholder-[#1A1A1A]/60 font-medium focus:outline-none"
                                placeholder="Ask anything"
                                rows={1}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />

                            <div className="flex gap-2 pb-2 pr-2">
                                {/* Upload Button */}
                                <div className="relative group/btn flex flex-col items-center">
                                    <MagneticButton onClick={handleUploadClick} className="p-3 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors">
                                        {isUploading ? <Sparkles className="w-6 h-6 animate-spin" /> : <Plus className="w-6 h-6" />}
                                    </MagneticButton>
                                    <span className="absolute -bottom-10 bg-black text-white px-2 py-1 rounded text-[10px] uppercase tracking-widest opacity-0 group-hover/btn:opacity-100 transition-opacity whitespace-nowrap">Upload</span>
                                </div>

                                {/* Send/Stop Button */}
                                <div className="relative group/btn flex flex-col items-center">
                                    <MagneticButton
                                        onClick={handleSend}
                                        className={cn(
                                            "p-3 rounded-full transition-all shadow-lg",
                                            input.trim() || isLoading
                                                ? "bg-[#1A1A1A] text-[#D4AF37] hover:scale-105"
                                                : "bg-white/10 text-white/30"
                                        )}
                                    >
                                        {isLoading ? <Square className="w-5 h-5 fill-current" /> : <Send className="w-5 h-5 ml-0.5" />}
                                    </MagneticButton>
                                    <span className="absolute -bottom-10 bg-black text-white px-2 py-1 rounded text-[10px] uppercase tracking-widest opacity-0 group-hover/btn:opacity-100 transition-opacity whitespace-nowrap">
                                        {isLoading ? "Stop" : "Send"}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </main>
        </div>
    );
}
