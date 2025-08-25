import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
	variant?: "primary" | "secondary" | "ghost" | "outline";
	size?: "sm" | "md" | "lg";
	icon?: React.ReactNode;
	loading?: boolean;
};

export default function Button({ 
	variant = "primary", 
	size = "md", 
	className, 
	disabled, 
	loading,
	icon,
	children,
	...props 
}: ButtonProps) {
	const baseClasses = [
		"inline-flex items-center justify-center select-none font-semibold",
		"transition-all duration-300 ease-out",
		"focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/20",
		"disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none",
		"relative overflow-hidden group",
	];

	const sizeClasses = {
		sm: "px-3 py-2 text-sm rounded-lg gap-1.5",
		md: "px-5 py-3 text-base rounded-xl gap-2",
		lg: "px-7 py-4 text-lg rounded-2xl gap-3",
	};

	const variantClasses = {
		primary: [
			"text-white bg-gradient-to-br from-primary via-primary to-[#B89273]",
			"shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/35",
			"hover:scale-[1.02] active:scale-[0.98]",
			"before:absolute before:inset-0 before:bg-gradient-to-r before:from-white/0 before:via-white/10 before:to-white/0",
			"before:translate-x-[-100%] hover:before:translate-x-[100%] before:transition-transform before:duration-700",
		],
		secondary: [
			"text-primary bg-primary/10 border-2 border-primary/20",
			"hover:bg-primary/20 hover:border-primary/30",
			"hover:scale-[1.02] active:scale-[0.98]",
			"shadow-sm hover:shadow-md",
		],
		ghost: [
			"text-primary bg-transparent",
			"hover:bg-primary/10 active:bg-primary/15",
			"hover:scale-[1.02] active:scale-[0.98]",
		],
		outline: [
			"text-text bg-white border-2 border-border",
			"hover:border-primary/30 hover:bg-primary/5",
			"hover:scale-[1.02] active:scale-[0.98]",
			"shadow-sm hover:shadow-md",
		],
	};

	const isDisabled = disabled || loading;

	const classes = [
		...baseClasses,
		sizeClasses[size],
		...variantClasses[variant],
		isDisabled && "transform-none hover:scale-100 active:scale-100",
		className,
	].filter(Boolean).join(" ");

	return (
		<button {...props} className={classes} disabled={isDisabled}>
			{loading && (
				<div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
			)}
			{!loading && icon && <span className="shrink-0">{icon}</span>}
			{children && <span className={loading ? "opacity-70" : ""}>{children}</span>}
		</button>
	);
}
