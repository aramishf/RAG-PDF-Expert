'use client';

import { UploadCloud, Plus } from 'lucide-react';
import MagneticButton from './ui/MagneticButton';
import { useRef } from 'react';
import { uploadFiles } from '@/lib/api';
import { motion } from 'framer-motion';

export default function PDFViewer() {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            try {
                await uploadFiles(Array.from(e.target.files));
                alert('Document uploaded to Aura Research.');
            } catch (err) {
                alert('Upload failed.');
            }
        }
    };

    return (
        <div className="h-full w-full bg-transparent relative flex items-center justify-center overflow-hidden">
            {/* Subtle Grain/Pattern Removed for Pure Black */}
            <div className="absolute inset-0 pointer-events-none" />

            {/* Upload Zone */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="text-center z-10"
            >
                <h2 className="font-serif text-3xl text-slate mb-2">Upload Zone</h2>
                <p className="text-slate/60 mb-8 font-sans">Drag & drop or select a PDF to analyze</p>

                <input
                    type="file"
                    multiple
                    accept=".pdf"
                    className="hidden"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                />

                <MagneticButton
                    onClick={handleUploadClick}
                    className="group relative inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#D4AF37] to-[#AA8C2C] text-[#1A1A1A] border border-[#F3E5AB]/30 rounded-full hover:to-[#D4AF37] hover:from-[#F3E5AB] transition-all shadow-lg shadow-[#D4AF37]/20 hover:shadow-[#D4AF37]/40 hover:-translate-y-1"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                    <span className="font-medium tracking-wide">Select Document</span>
                </MagneticButton>
            </motion.div>
        </div>
    );
}
