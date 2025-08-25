"use client";
import React from "react";

type CheckboxProps = {
	label?: string;
	checked: boolean;
	onChange: (v: boolean) => void;
	disabled?: boolean;
	size?: "sm" | "md" | "lg";
	description?: string;
};

export default function Checkbox({ 
	label, 
	checked, 
	onChange, 
	disabled = false,
	size = "md",
	description
}: CheckboxProps) {
	const sizeClasses = {
		sm: "w-4 h-4",
		md: "w-5 h-5", 
		lg: "w-6 h-6"
	};

	const textSizeClasses = {
		sm: "text-sm",
		md: "text-base",
		lg: "text-lg"
	};

	return (
		<label className={`
			group flex items-start gap-3 my-2 cursor-pointer select-none
			${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary/5'} 
			transition-all duration-200 rounded-lg p-2 -m-2
		`}>
			<div className="relative flex-shrink-0">
				<input 
					type="checkbox" 
					className="sr-only" 
					checked={checked} 
					onChange={(e) => !disabled && onChange(e.target.checked)}
					disabled={disabled}
				/>
				<div className={`
					${sizeClasses[size]} rounded-lg border-2 transition-all duration-300
					flex items-center justify-center
					${checked 
						? 'bg-gradient-to-br from-primary to-primary/80 border-primary shadow-lg shadow-primary/25' 
						: 'bg-white border-border hover:border-primary/50'
					}
					${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}
				`}>
					{checked && (
						<svg 
							className="w-3 h-3 text-white animate-[scale-in_0.2s_ease-out]" 
							fill="none" 
							stroke="currentColor" 
							viewBox="0 0 24 24"
						>
							<path 
								strokeLinecap="round" 
								strokeLinejoin="round" 
								strokeWidth={3} 
								d="M5 13l4 4L19 7" 
							/>
						</svg>
					)}
				</div>
			</div>
			
			{(label || description) && (
				<div className="flex-1">
					{label && (
						<span className={`
							${textSizeClasses[size]} text-text font-medium
							group-hover:text-primary transition-colors duration-200
						`}>
							{label}
						</span>
					)}
					{description && (
						<div className="text-lightText text-sm mt-1">
							{description}
						</div>
					)}
				</div>
			)}
		</label>
	);
}


