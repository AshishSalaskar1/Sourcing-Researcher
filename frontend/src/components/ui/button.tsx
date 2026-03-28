import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "ghost";
};

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  default: "button button-primary",
  secondary: "button button-secondary",
  ghost: "button button-ghost",
};

export function Button({
  className,
  variant = "default",
  ...props
}: ButtonProps) {
  return <button className={cn(variantClasses[variant], className)} {...props} />;
}

