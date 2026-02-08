import React from 'react'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

interface CardSubComponentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`rounded-lg border border-gray-200 bg-white shadow-sm ${className}`}
      {...props}
    />
  )
)
Card.displayName = 'Card'

export const CardHeader = React.forwardRef<HTMLDivElement, CardSubComponentProps>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`px-6 py-4 border-b border-gray-200 ${className}`} {...props} />
  )
)
CardHeader.displayName = 'CardHeader'

export const CardTitle = React.forwardRef<HTMLHeadingElement, CardSubComponentProps>(
  ({ className = '', ...props }, ref) => (
    <h2
      ref={ref as React.Ref<HTMLHeadingElement>}
      className={`text-lg font-semibold text-gray-900 ${className}`}
      {...(props as React.HTMLAttributes<HTMLHeadingElement>)}
    />
  )
)
CardTitle.displayName = 'CardTitle'

export const CardDescription = React.forwardRef<HTMLParagraphElement, CardSubComponentProps>(
  ({ className = '', ...props }, ref) => (
    <p
      ref={ref as React.Ref<HTMLParagraphElement>}
      className={`text-sm text-gray-500 ${className}`}
      {...(props as React.HTMLAttributes<HTMLParagraphElement>)}
    />
  )
)
CardDescription.displayName = 'CardDescription'

export const CardContent = React.forwardRef<HTMLDivElement, CardSubComponentProps>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`px-6 py-4 ${className}`} {...props} />
  )
)
CardContent.displayName = 'CardContent'
