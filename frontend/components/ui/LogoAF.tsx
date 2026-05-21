import React from "react";

type AfLogoProps = {
    className?: string;
};

export default function LogoAF({
    className = "",
}: AfLogoProps) {
    return (
        <img
            src="/logo_af.png"
            alt="AF Logo"
            className={`${className} object-contain`}
            style={{ aspectRatio: 'auto' }}
        />
    );
}
