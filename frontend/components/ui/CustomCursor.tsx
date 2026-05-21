'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export default function CustomCursor() {
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const [cursorState, setCursorState] = useState<'default' | 'pointer' | 'text'>('default');
    const [ripples, setRipples] = useState<{ x: number, y: number, id: number }[]>([]);

    useEffect(() => {
        const updateMousePosition = (e: MouseEvent) => {
            setMousePosition({ x: e.clientX, y: e.clientY });
        };

        const handleMouseOver = (e: MouseEvent) => {
            const target = e.target as HTMLElement;

            // Check for buttons/links
            const isClickable = target.tagName === 'BUTTON' || target.tagName === 'A' || target.closest('button') || target.closest('a');
            // Check for text inputs
            const isText = target.tagName === 'P' || target.tagName === 'SPAN' || target.tagName === 'H1' || target.tagName === 'H2' || target.tagName === 'H3' || target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

            if (isClickable) {
                setCursorState('pointer');
            } else if (isText) {
                setCursorState('text');
            } else {
                setCursorState('default');
            }
        };

        const handleClick = (e: MouseEvent) => {
            setRipples(prev => [...prev, { x: e.clientX, y: e.clientY, id: Date.now() }]);
            setTimeout(() => {
                setRipples(prev => prev.slice(1));
            }, 600);
        };

        window.addEventListener('mousemove', updateMousePosition);
        window.addEventListener('mouseover', handleMouseOver);
        window.addEventListener('click', handleClick);

        return () => {
            window.removeEventListener('mousemove', updateMousePosition);
            window.removeEventListener('mouseover', handleMouseOver);
            window.removeEventListener('click', handleClick);
        };
    }, []);

    return (
        <>
            {/* Main Cursor Blob */}
            <motion.div
                className={cn(
                    "fixed top-0 left-0 pointer-events-none z-[100]",
                    cursorState === 'text' ? "bg-white rounded-sm" : "rounded-full bg-[#D4AF37]"
                )}
                animate={{
                    x: mousePosition.x - (cursorState === 'text' ? 1 : 12),
                    y: mousePosition.y - (cursorState === 'text' ? 10 : 12),
                    width: cursorState === 'default' ? 24 : cursorState === 'pointer' ? 36 : 2,
                    height: cursorState === 'default' ? 24 : cursorState === 'pointer' ? 36 : 20,
                    opacity: cursorState === 'text' ? 0.6 : 0.8,
                }}
                transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 28,
                    mass: 0.5
                }}
            />

            {/* Click Ripples */}
            <AnimatePresence>
                {ripples.map(ripple => (
                    <motion.div
                        key={ripple.id}
                        initial={{ opacity: 0.5, scale: 0, x: ripple.x - 20, y: ripple.y - 20 }}
                        animate={{ opacity: 0, scale: 2 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.6 }}
                        className="fixed w-10 h-10 rounded-full bg-[#D4AF37] z-[99] pointer-events-none"
                    />
                ))}
            </AnimatePresence>
        </>
    );
}
