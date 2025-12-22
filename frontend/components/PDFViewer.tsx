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
        <div className="h-full w-full bg-cream/50 relative flex items-center justify-center overflow-hidden">
            {/* Subtle Grain/Pattern */}
            <div className="absolute inset-0 opacity-[0.05] pointer-events-none"
                style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%233B4953\' fill-opacity=\'1\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")' }}
            />

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
                    className="group relative inline-flex items-center gap-3 px-8 py-4 bg-sage text-white rounded-full hover:bg-[#7e9979] transition-all shadow-lg shadow-sage/20 hover:shadow-sage/40 hover:-translate-y-1"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                    <span className="font-medium tracking-wide">Select Document</span>
                </MagneticButton>
            </motion.div>
        </div>
    );
}
