import React, { useState, createContext, useContext } from 'react'

interface DialogContextType {
  open: boolean
  setOpen: (value: boolean) => void
}

const DialogContext = createContext<DialogContextType | undefined>(undefined)

interface DialogProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children: React.ReactNode
}

export const Dialog = ({ open = false, onOpenChange, children }: DialogProps) => {
  const [internalOpen, setInternalOpen] = useState(open)

  const handleOpenChange = (newOpen: boolean) => {
    setInternalOpen(newOpen)
    onOpenChange?.(newOpen)
  }

  return (
    <DialogContext.Provider value={{ open: open || internalOpen, setOpen: handleOpenChange }}>
      {children}
    </DialogContext.Provider>
  )
}

interface DialogTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
}

export const DialogTrigger = React.forwardRef<HTMLButtonElement, DialogTriggerProps>(
  ({ children, onClick, ...props }, ref) => {
    const context = useContext(DialogContext)

    if (!context) {
      throw new Error('DialogTrigger must be used within Dialog')
    }

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      context.setOpen(true)
      onClick?.(e)
    }

    return (
      <button ref={ref} onClick={handleClick} {...props}>
        {children}
      </button>
    )
  }
)
DialogTrigger.displayName = 'DialogTrigger'

interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const DialogContent = React.forwardRef<HTMLDivElement, DialogContentProps>(
  ({ children, className = '', ...props }, ref) => {
    const context = useContext(DialogContext)

    if (!context) {
      throw new Error('DialogContent must be used within Dialog')
    }

    if (!context.open) {
      return null
    }

    return (
      <>
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => context.setOpen(false)}
        />

        {/* Dialog */}
        <div
          ref={ref}
          className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-lg z-50 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto ${className}`}
          {...props}
        >
          {children}
        </div>
      </>
    )
  }
)
DialogContent.displayName = 'DialogContent'

interface DialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const DialogHeader = React.forwardRef<HTMLDivElement, DialogHeaderProps>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`px-8 py-4 border-b border-gray-200 ${className}`} {...props} />
  )
)
DialogHeader.displayName = 'DialogHeader'

interface DialogTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode
}

export const DialogTitle = React.forwardRef<HTMLHeadingElement, DialogTitleProps>(
  ({ className = '', ...props }, ref) => (
    <h2
      ref={ref}
      className={`text-lg font-semibold text-gray-900 ${className}`}
      {...(props as React.HTMLAttributes<HTMLHeadingElement>)}
    />
  )
)
DialogTitle.displayName = 'DialogTitle'

interface DialogDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode
}

export const DialogDescription = React.forwardRef<HTMLParagraphElement, DialogDescriptionProps>(
  ({ className = '', ...props }, ref) => (
    <p
      ref={ref}
      className={`text-sm text-gray-500 ${className}`}
      {...(props as React.HTMLAttributes<HTMLParagraphElement>)}
    />
  )
)
DialogDescription.displayName = 'DialogDescription'

interface DialogBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const DialogBody = React.forwardRef<HTMLDivElement, DialogBodyProps>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`px-6 py-4 ${className}`} {...props} />
  )
)
DialogBody.displayName = 'DialogBody'

interface DialogFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const DialogFooter = React.forwardRef<HTMLDivElement, DialogFooterProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`px-8 py-4 border-t border-gray-200 flex justify-end gap-2 ${className}`}
      {...props}
    />
  )
)
DialogFooter.displayName = 'DialogFooter'
