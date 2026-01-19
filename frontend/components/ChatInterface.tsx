import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, Bot, Plus, ArrowUp } from 'lucide-react';
import MagneticButton from './ui/MagneticButton';
import LogoAF from './ui/LogoAF';
import { sendChat, uploadFiles, type ChatMessage } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
    const [uploadedFiles, setUploadedFiles] = useState<Set<string>>(new Set());
    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;
        const question = input;
        setInput('');
        setIsLoading(true);

        setMessages(prev => [...prev, { role: 'user', content: question }]);

        // Add thinking indicator
        setMessages(prev => [...prev, { role: 'assistant', content: 'Thinking...' }]);

        try {
            const response = await sendChat(question);
            // Remove thinking indicator and add real response
            setMessages(prev => {
                const withoutThinking = prev.slice(0, -1);
                return [...withoutThinking, {
                    role: 'assistant',
                    content: response.answer,
                    citations: response.citations
                }];
            });
        } catch (error) {
            // Remove thinking indicator and show error
            setMessages(prev => {
                const withoutThinking = prev.slice(0, -1);
                return [...withoutThinking, {
                    role: 'assistant',
                    content: "I encountered an error processing your question. Please try again or upload documents if you haven't already."
                }];
            });
        } finally {
            setIsLoading(false);
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

            // Filter out already uploaded files
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

                // Add to uploaded files set
                setUploadedFiles(prev => new Set([...prev, ...newFiles.map(f => f.name)]));

                const fileNames = newFiles.map(f => f.name).join(', ');
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `Documents processed and ready for analysis:\n\n${newFiles.map(f => `• ${f.name}`).join('\n')}`
                }]);
            } catch {
                alert('Upload failed');
            } finally {
                setIsUploading(false);
                setUploadingFiles([]);
            }
        }
    };

    return (
        <div className="h-full w-full flex flex-col relative overflow-hidden bg-transparent font-sans">

            {/* Header */}
            <div className="absolute top-0 left-0 w-full h-24 flex items-center justify-between px-8 z-10">
                <div className="flex items-center gap-4 group cursor-default">
                    <div className="group-hover:scale-105 transition-transform duration-500 drop-shadow-sm">
                        {/* Reduced Size ~20% (w-10 instead of w-12) */}
                        <LogoAF className="w-10 h-10" />
                    </div>
                    <div>
                        {/* Clean Brand Name Only - Charcoal/Dark for contrast or White if BG is dark? 
                            BG is Forest (#5A7863). Dark Text might have low contrast. User said "Keep... text as is". 
                            Previous was Forest/Charcoal. On Forest BG, Charcoal is low contrast.
                            User requested Canvas = Forest Green. 
                            Let's use White/Cream for text to be visible on Forest Green.
                        */}
                        <h1 className="text-xl text-white/90 font-bold tracking-wide uppercase leading-none font-sans">AI Research Assistant</h1>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto w-full px-6 md:px-20 pt-32 pb-40" ref={scrollRef}>

                {!messages.length && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="h-full flex flex-col items-center justify-center text-center space-y-8 -mt-20"
                    >
                        <div className="relative">
                            <div className="absolute inset-0 bg-transparent" />
                            <img
                                src="/ai_avatar.png"
                                alt="AI Assistant"
                                className="w-40 h-40 relative z-10 drop-shadow-2xl object-cover rounded-2xl"
                            />
                        </div>

                        <h2 className="text-xl md:text-2xl font-light text-white/90 tracking-wide max-w-xl">
                            Upload your documents to instantly extract insights
                        </h2>

                        {/* Upload Progress - Compact version for empty state */}
                        {isUploading && (
                            <div className="flex items-center gap-2 bg-white/10 rounded-full px-4 py-2 text-sm">
                                <div className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"></div>
                                <span className="text-white/90 font-medium">
                                    Uploading {uploadingFiles.length} document{uploadingFiles.length !== 1 ? 's' : ''}...
                                </span>
                            </div>
                        )}

                        {/* Input Bar Centered Here when Empty */}
                        <div className="w-full max-w-2xl mt-8">
                            {/* Input Container: Dark Green/Grey Background */}
                            {/* Input Container: Gold Gradient Bar */}
                            <div className="bg-gradient-to-r from-[#e3c788] via-[#d4af37] to-[#aa8c2c] rounded-3xl p-2 pl-6 flex items-end gap-4 shadow-2xl shadow-[#D4AF37]/20 border border-[#F3E5AB]/40 ring-1 ring-[#D4AF37]/20 focus-within:ring-[#F3E5AB]/50 transition-all duration-300">

                                <input
                                    type="file"
                                    multiple
                                    accept=".pdf"
                                    className="hidden"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                />

                                <textarea
                                    className="flex-1 bg-transparent border-0 focus:ring-0 resize-none max-h-40 min-h-[48px] py-3 text-base text-[#1A1A1A] placeholder-[#1A1A1A]/60 font-medium focus:outline-none"
                                    placeholder="Ask anything"
                                    rows={1}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                />

                                <div className="flex gap-2 pb-2 pr-2">
                                    {/* Upload Icon: Plus (+) White */}
                                    <div className="relative group/btn flex flex-col items-center">
                                        <MagneticButton
                                            onClick={handleUploadClick}
                                            className="p-3 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                                        >
                                            <Plus className="w-6 h-6" />
                                        </MagneticButton>
                                        <span className="absolute -bottom-10 bg-black text-white px-2 py-1 rounded text-[10px] uppercase tracking-widest opacity-0 group-hover/btn:opacity-100 transition-opacity whitespace-nowrap">
                                            Upload
                                        </span>
                                    </div>

                                    {/* Send Icon: Paper Plane White */}
                                    <div className="relative group/btn flex flex-col items-center">
                                        <MagneticButton
                                            onClick={handleSend}
                                            className={cn(
                                                "p-3 rounded-full transition-all shadow-lg",
                                                input.trim()
                                                    ? "bg-[#1A1A1A] text-[#D4AF37] hover:scale-105"
                                                    : "bg-white/10 text-white/30"
                                            )}
                                        >
                                            <Send className="w-5 h-5 ml-0.5" />
                                        </MagneticButton>
                                        <span className="absolute -bottom-10 bg-black text-white px-2 py-1 rounded text-[10px] uppercase tracking-widest opacity-0 group-hover/btn:opacity-100 transition-opacity whitespace-nowrap">
                                            Send
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </motion.div>
                )}

                <AnimatePresence initial={false}>
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={cn("flex gap-6 mb-12 max-w-4xl mx-auto", msg.role === 'user' ? "flex-row-reverse" : "")}
                        >
                            <div className={cn(
                                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold border",
                                msg.role === 'assistant' ? "bg-white/10 border-white/20 text-white" : "bg-black/40 border-black/50 text-white"
                            )}>
                                {msg.role === 'assistant' ? "AF" : "AF"}
                            </div>

                            <div className={cn("max-w-[85%]", msg.role === 'user' ? "text-right" : "")}>
                                <div className={cn(
                                    "text-lg leading-relaxed",
                                    msg.role === 'user'
                                        ? "text-white font-medium"
                                        : "text-white/90",
                                    msg.content === 'Thinking...' && "animate-pulse"
                                )}>
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                </div>

                                {msg.citations && msg.citations.length > 0 && msg.content !== 'Thinking...' && (
                                    <div className="flex flex-wrap gap-2 mt-4 pl-1">
                                        {msg.citations.map((cite, i) => {
                                            // Create abbreviation from book name
                                            const bookName = cite.source?.replace('.pdf', '') || 'Unknown';
                                            const abbreviation = bookName
                                                .split('-')
                                                .map(word => word[0]?.toUpperCase())
                                                .join('');

                                            return (
                                                <span
                                                    key={i}
                                                    className="text-xs bg-white/10 hover:bg-white/15 text-white/90 px-3 py-1.5 rounded font-bold tracking-wider uppercase cursor-default transition-colors"
                                                    title={`${bookName} - Page ${cite.page}`}
                                                >
                                                    {abbreviation}: P.{cite.page}
                                                </span>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Fixed Input Bar (Only visible when messages exist) */}
            {messages.length > 0 && (
                <div className="absolute bottom-6 left-0 w-full px-8 z-20">
                    <div className="max-w-3xl mx-auto relative">
                        {/* Upload Progress - Compact version above input */}
                        {isUploading && (
                            <div className="mb-2 flex justify-center">
                                <div className="flex items-center gap-2 bg-white/10 rounded-full px-4 py-2 text-sm">
                                    <div className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"></div>
                                    <span className="text-white/90 font-medium">
                                        Uploading {uploadingFiles.length} document{uploadingFiles.length !== 1 ? 's' : ''}...
                                    </span>
                                </div>
                            </div>
                        )}
                        {/* Input Container: Dark Green/Grey Background */}
                        {/* Input Container: Gold Gradient Bar */}
                        <div className="bg-gradient-to-r from-[#e3c788] via-[#d4af37] to-[#aa8c2c] rounded-3xl p-2 pl-6 flex items-end gap-4 shadow-2xl shadow-[#D4AF37]/20 border border-[#F3E5AB]/40 ring-1 ring-[#D4AF37]/20 focus-within:ring-[#F3E5AB]/50 transition-all duration-300">

                            <input
                                type="file"
                                multiple
                                accept=".pdf"
                                className="hidden"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                            />

                            <textarea
                                className="flex-1 bg-transparent border-0 focus:ring-0 resize-none max-h-40 min-h-[48px] py-3 text-base text-[#1A1A1A] placeholder-[#1A1A1A]/60 font-medium focus:outline-none"
                                placeholder="Ask anything"
                                rows={1}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />

                            <div className="flex gap-2 pb-2 pr-2">
                                {/* Upload Icon: Plus (+) White */}
                                <div className="relative group/btn flex flex-col items-center">
                                    <MagneticButton
                                        onClick={handleUploadClick}
                                        className="p-3 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                                    >
                                        <Plus className="w-6 h-6" />
                                    </MagneticButton>
                                    <span className="absolute -bottom-10 bg-black text-white px-2 py-1 rounded text-[10px] uppercase tracking-widest opacity-0 group-hover/btn:opacity-100 transition-opacity whitespace-nowrap">
                                        Upload
                                    </span>
                                </div>

                                {/* Send Icon: Paper Plane White */}
                                <div className="relative group/btn flex flex-col items-center">
                                    <MagneticButton
                                        onClick={handleSend}
                                        className={cn(
                                            "p-3 rounded-full transition-all shadow-lg",
                                            input.trim()
                                                ? "bg-[#1A1A1A] text-[#D4AF37] hover:scale-105"
                                                : "bg-white/10 text-white/30"
                                        )}
                                    >
                                        <Send className="w-5 h-5 ml-0.5" />
                                    </MagneticButton>
                                    <span className="absolute -bottom-10 bg-black text-white px-2 py-1 rounded text-[10px] uppercase tracking-widest opacity-0 group-hover/btn:opacity-100 transition-opacity whitespace-nowrap">
                                        Send
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
