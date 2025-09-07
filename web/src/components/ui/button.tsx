import type { ButtonHTMLAttributes } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cn } from '../../utils/cn';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  asChild?: boolean;
}

export function Button({ variant = 'primary', className, asChild, ...props }: ButtonProps) {
  const variants: Record<string, string> = {
    primary:
      'bg-planifit-600 text-white hover:bg-planifit-700 focus-visible:ring-planifit-500',
    secondary:
      'border border-planifit-600 text-planifit-600 hover:bg-planifit-50 focus-visible:ring-planifit-500',
    ghost: 'text-planifit-600 hover:bg-planifit-50 focus-visible:ring-planifit-500',
  };
  const Comp = asChild ? Slot : 'button';
  return (
    <Comp
      className={cn(
        'rounded-md px-4 py-2 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}

export default Button;
