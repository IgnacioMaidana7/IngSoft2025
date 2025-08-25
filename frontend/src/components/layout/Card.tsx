import React from "react";

type CardProps = {
	children: React.ReactNode;
	className?: string;
	variant?: "default" | "elevated" | "glass" | "gradient";
	padding?: "none" | "sm" | "md" | "lg";
	hover?: boolean;
};

export default function Card({ 
	children, 
	className, 
	variant = "default",
	padding = "md",
	hover = true
}: CardProps) {
	const baseClasses = [
		"border border-border rounded-3xl transition-all duration-500 ease-out",
		"backdrop-blur-sm supports-[backdrop-filter]:backdrop-blur-sm",
	];

	const variantClasses = {
		default: [
			"bg-white/95",
			"shadow-lg shadow-black/5",
			hover && "hover:shadow-xl hover:shadow-primary/10 hover:-translate-y-1",
		],
		elevated: [
			"bg-gradient-to-br from-white via-white to-primary/5",
			"shadow-xl shadow-primary/20",
			hover && "hover:shadow-2xl hover:shadow-primary/25 hover:-translate-y-2",
		],
		glass: [
			"bg-white/80 border-white/30",
			"shadow-lg shadow-black/5",
			hover && "hover:bg-white/90 hover:shadow-xl hover:shadow-primary/10",
		],
		gradient: [
			"bg-gradient-to-br from-white via-primary/5 to-primary/10",
			"border-primary/20",
			"shadow-lg shadow-primary/10",
			hover && "hover:shadow-xl hover:shadow-primary/20 hover:-translate-y-1",
		],
	};

	const paddingClasses = {
		none: "p-0",
		sm: "p-4",
		md: "p-6",
		lg: "p-8",
	};

	const classes = [
		...baseClasses,
		...variantClasses[variant],
		paddingClasses[padding],
		"group",
		className,
	].filter(Boolean).join(" ");

	return (
		<div className={classes}>
			{children}
		</div>
	);
}


