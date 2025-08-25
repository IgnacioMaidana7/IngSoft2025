"use client";
import React from "react";
import Link from "next/link";

type HomeButtonProps = {
	title: string;
	icon?: string;
	href?: string;
	onClick?: () => void;
	description?: string;
	disabled?: boolean;
};

export default function HomeButton({ 
	title, 
	icon, 
	href, 
	onClick, 
	description,
	disabled = false
}: HomeButtonProps) {
	const content = (
		<div className={`
			group relative w-full overflow-hidden
			bg-gradient-to-br from-white via-white to-primary/5
			border-2 border-border/60 rounded-2xl p-6 mb-4
			shadow-lg shadow-black/5
			transition-all duration-500 ease-out
			${!disabled && 'hover:shadow-xl hover:shadow-primary/15 hover:-translate-y-1 hover:border-primary/30'}
			${!disabled && 'active:scale-[0.98] active:translate-y-0'}
			${disabled && 'opacity-50 cursor-not-allowed'}
			backdrop-blur-sm
		`}>
			{/* Gradient overlay that appears on hover */}
			<div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
			
			{/* Icon with modern styling */}
			<div className="relative flex items-center gap-4">
				<div className={`
					w-14 h-14 bg-gradient-to-br from-primary to-primary/80
					text-white rounded-2xl 
					flex items-center justify-center text-2xl
					shadow-lg shadow-primary/25
					transition-all duration-500
					${!disabled && 'group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-xl group-hover:shadow-primary/35'}
				`}>
					{icon ?? "📦"}
				</div>
				
				<div className="flex-1">
					<div className="text-text font-bold text-lg mb-1 group-hover:text-primary transition-colors duration-300">
						{title}
					</div>
					{description && (
						<div className="text-lightText text-sm">
							{description}
						</div>
					)}
				</div>
				
				{/* Arrow indicator */}
				<div className={`
					text-primary/60 transition-all duration-300
					${!disabled && 'group-hover:text-primary group-hover:translate-x-1'}
				`}>
					<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
					</svg>
				</div>
			</div>
		</div>
	);

	if (disabled) {
		return <div className="cursor-not-allowed">{content}</div>;
	}

	if (href) {
		return (
			<Link 
				href={href} 
				className="block no-underline" 
				onClick={onClick}
			>
				{content}
			</Link>
		);
	}

	return (
		<button 
			className="w-full bg-transparent border-0 p-0 cursor-pointer text-left" 
			onClick={onClick}
		>
			{content}
		</button>
	);
}


