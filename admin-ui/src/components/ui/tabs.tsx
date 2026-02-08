import React, { useState, createContext, useContext } from 'react'

interface TabsContextType {
  activeTab: string
  setActiveTab: (value: string) => void
}

const TabsContext = createContext<TabsContextType | undefined>(undefined)

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue: string
  children: React.ReactNode
}

export const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ defaultValue, children, className = '', ...props }, ref) => {
    const [activeTab, setActiveTab] = useState(defaultValue)

    return (
      <TabsContext.Provider value={{ activeTab, setActiveTab }}>
        <div ref={ref} className={className} {...props}>
          {children}
        </div>
      </TabsContext.Provider>
    )
  }
)
Tabs.displayName = 'Tabs'

interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const TabsList = React.forwardRef<HTMLDivElement, TabsListProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`flex border-b border-gray-200 ${className}`}
      {...props}
    />
  )
)
TabsList.displayName = 'TabsList'

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
  children: React.ReactNode
}

export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ value, children, className = '', ...props }, ref) => {
    const context = useContext(TabsContext)

    if (!context) {
      throw new Error('TabsTrigger must be used within Tabs')
    }

    const { activeTab, setActiveTab } = context
    const isActive = activeTab === value

    return (
      <button
        ref={ref}
        onClick={() => setActiveTab(value)}
        className={`px-4 py-2 border-b-2 font-medium transition-colors ${
          isActive
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        } ${className}`}
        {...props}
      >
        {children}
      </button>
    )
  }
)
TabsTrigger.displayName = 'TabsTrigger'

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  children: React.ReactNode
}

export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ value, children, className = '', ...props }, ref) => {
    const context = useContext(TabsContext)

    if (!context) {
      throw new Error('TabsContent must be used within Tabs')
    }

    const { activeTab } = context

    if (activeTab !== value) {
      return null
    }

    return (
      <div ref={ref} className={className} {...props}>
        {children}
      </div>
    )
  }
)
TabsContent.displayName = 'TabsContent'
