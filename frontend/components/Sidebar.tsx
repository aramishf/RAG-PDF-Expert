'use client';

import { Home, UploadCloud, Settings, BookOpen, Sparkles } from 'lucide-react';
import MagneticButton from './ui/MagneticButton';
import { cn } from '@/lib/utils';

export default function Sidebar() {
    return (
        <nav className="h-screen w-[80px] flex flex-col items-center py-8 glass border-r-0 z-40">

            {/* Logo: Abstract Orbital */}
            <div className="mb-12 relative group cursor-pointer">
                <div className="absolute inset-0 bg-sage blur-lg opacity-40 group-hover:opacity-60 transition-opacity" />
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sage to-slate flex items-center justify-center relative overflow-hidden">
                    <Sparkles className="text-cream w-5 h-5" />
                    <div className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                </div>
            </div>

            <div className="flex flex-col gap-6 flex-1 items-center">
                <NavIcon icon={<Home className="w-5 h-5" />} tooltip="Home" active />
                <NavIcon icon={<BookOpen className="w-5 h-5" />} tooltip="Library" />
                <NavIcon icon={<UploadCloud className="w-5 h-5" />} tooltip="Upload" />
            </div>

            <div className="mt-auto">
                <NavIcon icon={<Settings className="w-5 h-5" />} tooltip="Settings" />
            </div>
        </nav>
    );
}

function NavIcon({ icon, tooltip, active }: { icon: React.ReactNode, tooltip: string, active?: boolean }) {
    return (
        <MagneticButton className={cn(
            "p-3 rounded-2xl transition-all duration-300 relative group",
            active ? "bg-white/10 text-sage shadow-inner" : "text-slate/60 hover:text-slate hover:bg-white/5"
        )}>
            {icon}
            <span className="absolute left-14 bg-slate text-cream text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {tooltip}
            </span>
        </MagneticButton>
    )
}
