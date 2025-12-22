import React from "react";

type AfLogoProps = {
    className?: string;
};

export default function LogoAF({
    className = "",
}: AfLogoProps) {
    return (
        <img
            src="/af-logo-transparent.png?v=5"
            alt="AF Logo"
            className={`${className} object-contain`}
            style={{ aspectRatio: '16/9' }}
        />
    );
}
