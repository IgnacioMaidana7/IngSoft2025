import React, { useState, useId } from "react";

interface SelectOption {
  label: string;
  value: string;
}

type Props = React.SelectHTMLAttributes<HTMLSelectElement> & { 
	label?: string;
	error?: string;
	helper?: string;
	options: SelectOption[];
};

export default function Select({ 
	label, 
	id, 
	className, 
	error,
	helper,
	options,
	onFocus,
	onBlur,
	...props 
}: Props) {
	const [isFocused, setIsFocused] = useState(false);
	const generatedId = useId();
	const inputId = id ?? generatedId;
	const hasError = !!error;

	const handleFocus = (e: React.FocusEvent<HTMLSelectElement>) => {
		setIsFocused(true);
		onFocus?.(e);
	};

	const handleBlur = (e: React.FocusEvent<HTMLSelectElement>) => {
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
				<select
					id={inputId}
					{...props}
					onFocus={handleFocus}
					onBlur={handleBlur}
					className={[
						"w-full py-4 px-4 rounded-2xl outline-none transition-all duration-300",
						"border-2 bg-white/80 backdrop-blur-sm",
						"text-text",
						hasError
							? "border-red-300 focus:border-red-500 focus:ring-4 focus:ring-red-100"
							: isFocused
								? "border-primary focus:border-primary focus:ring-4 focus:ring-primary/10 shadow-lg shadow-primary/10"
								: "border-border hover:border-primary/30 focus:border-primary focus:ring-4 focus:ring-primary/10",
						"hover:bg-white/90 focus:bg-white cursor-pointer",
						className,
					].filter(Boolean).join(" ")}
				>
					<option value="">Seleccionar...</option>
					{options.map((option) => (
						<option key={option.value} value={option.value}>
							{option.label}
						</option>
					))}
				</select>
			</div>
			
			{(error || helper) && (
				<div className={`mt-2 text-sm ${hasError ? 'text-red-600' : 'text-lightText'}`}>
					{error || helper}
				</div>
			)}
		</div>
	);
}
