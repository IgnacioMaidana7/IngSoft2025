import React from "react";

type ContainerProps = {
	children: React.ReactNode;
	className?: string;
	size?: "sm" | "md" | "lg" | "xl" | "full";
	padding?: boolean;
	animate?: boolean;
};

export default function Container({ 
	children, 
	className,
	size = "lg",
	padding = true,
	animate = true
}: ContainerProps) {
	const sizeClasses = {
		sm: "max-w-2xl",      // 672px
		md: "max-w-4xl",      // 896px  
		lg: "max-w-6xl",      // 1152px
		xl: "max-w-7xl",      // 1280px
		full: "max-w-none"
	};

	const classes = [
		"w-full mx-auto",
		sizeClasses[size],
		padding && "px-4 sm:px-6 lg:px-8 py-6",
		animate && "animate-[fadeInUp_0.6s_ease-out]",
		className
	].filter(Boolean).join(" ");

	return <div className={classes}>{children}</div>;
}


