import React from 'react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg'
  children: React.ReactNode
}

const variantClasses = {
  default: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
  destructive: 'bg-red-600 hover:bg-red-700 text-white',
  outline: 'border border-gray-300 hover:bg-gray-100 text-gray-900',
  ghost: 'hover:bg-gray-100 text-gray-900',
}

const sizeClasses = {
  default: 'px-4 py-2 text-sm',
  sm: 'px-2 py-1 text-xs',
  lg: 'px-8 py-3 text-base',
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'default', size = 'default', ...props }, ref) => {
    const baseClasses =
      'inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
    const variantClass = variantClasses[variant]
    const sizeClass = sizeClasses[size]

    return (
      <button
        ref={ref}
        className={`${baseClasses} ${variantClass} ${sizeClass} ${className}`}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
