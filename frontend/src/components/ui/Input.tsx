import React, { useState, useId } from "react";

type Props = React.InputHTMLAttributes<HTMLInputElement> & { 
	label?: string;
	error?: string;
	helper?: string;
	icon?: React.ReactNode;
	suffix?: React.ReactNode;
};

export default function Input({ 
	label, 
	id, 
	className, 
	error,
	helper,
	icon,
	suffix,
	onFocus,
	onBlur,
	...props 
}: Props) {
	const [isFocused, setIsFocused] = useState(false);
	const generatedId = useId();
	const inputId = id ?? generatedId;
	const hasError = !!error;

	const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
		setIsFocused(true);
		onFocus?.(e);
	};

	const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
		setIsFocused(false);
		onBlur?.(e);
	};

	return (
		<div className="w-full mb-5">
			{label && (
				<label 
					htmlFor={inputId} 
					className={`block mb-2 text-sm font-medium transition-colors duration-200 ${
						hasError ? 'text-red-600' : isFocused ? 'text-primary' : 'text-text'
					}`}
				>
					{label}
				</label>
			)}
			
			<div className="relative">
				{icon && (
					<div className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${
						hasError ? 'text-red-500' : isFocused ? 'text-primary' : 'text-lightText'
					}`}>
						{icon}
					</div>
				)}
				
				<input
					id={inputId}
					{...props}
					onFocus={handleFocus}
					onBlur={handleBlur}
					className={[
						"w-full py-4 rounded-2xl outline-none transition-all duration-300",
						"border-2 bg-white/80 backdrop-blur-sm",
						"placeholder:text-lightText/60 text-text",
						icon ? "pl-12 pr-4" : "px-4",
						suffix ? "pr-12" : "",
						hasError
							? "border-red-300 focus:border-red-500 focus:ring-4 focus:ring-red-100"
							: isFocused
								? "border-primary focus:border-primary focus:ring-4 focus:ring-primary/10 shadow-lg shadow-primary/10"
								: "border-border hover:border-primary/30 focus:border-primary focus:ring-4 focus:ring-primary/10",
						"hover:bg-white/90 focus:bg-white",
						className,
					].filter(Boolean).join(" ")}
				/>
				
				{suffix && (
					<div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-lightText">
						{suffix}
					</div>
				)}
			</div>
			
			{(error || helper) && (
				<div className={`mt-2 text-sm ${hasError ? 'text-red-600' : 'text-lightText'}`}>
					{error || helper}
				</div>
			)}
		</div>
	);
}
