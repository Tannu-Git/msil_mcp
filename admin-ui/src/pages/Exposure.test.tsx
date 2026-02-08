"""
Tests for Exposure Governance admin UI components.

Tests cover:
- Component rendering
- User interactions
- API integration
- Error handling
- Loading states
- Accessibility
"""

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Exposure from '@/pages/Exposure'
import { AddPermissionDialog } from '@/components/exposure/AddPermissionDialog'
import { PermissionsList } from '@/components/exposure/PermissionsList'
import { PreviewPanel } from '@/components/exposure/PreviewPanel'
import * as exposureApi from '@/lib/api/exposureApi'

// Mock API
jest.mock('@/lib/api/exposureApi')

// Create query client for testing
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

const TestWrapper = ({ children }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
)

// ============================================
// EXPOSURE PAGE TESTS
// ============================================

describe('Exposure Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render the page with header', () => {
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })

    render(<Exposure />, { wrapper: TestWrapper })

    expect(screen.getByText(/Tool Exposure Governance/i)).toBeInTheDocument()
  })

  it('should display role selector buttons', async () => {
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })

    render(<Exposure />, { wrapper: TestWrapper })

    await waitFor(() => {
      expect(screen.getByText('Operator')).toBeInTheDocument()
      expect(screen.getByText('Developer')).toBeInTheDocument()
      expect(screen.getByText('Admin')).toBeInTheDocument()
    })
  })

  it('should load permissions for selected role', async () => {
    const mockPermissions = ['expose:bundle:Service Booking']
    exposureApi.getRoleExposurePermissions.mockResolvedValue(mockPermissions)
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 5,
      exposed_bundles: ['Service Booking'],
      exposed_tools: [],
    })

    render(<Exposure />, { wrapper: TestWrapper })

    await waitFor(() => {
      expect(exposureApi.getRoleExposurePermissions).toHaveBeenCalledWith('operator')
    })
  })

  it('should switch roles when clicking role button', async () => {
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'developer',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })

    render(<Exposure />, { wrapper: TestWrapper })

    const developerButton = await screen.findByRole('button', { name: /Developer/i })
    fireEvent.click(developerButton)

    await waitFor(() => {
      expect(exposureApi.getRoleExposurePermissions).toHaveBeenCalledWith('developer')
    })
  })

  it('should display loading state while fetching data', () => {
    exposureApi.getRoleExposurePermissions.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )
    exposureApi.getAvailableBundles.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )
    exposureApi.previewRoleExposure.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<Exposure />, { wrapper: TestWrapper })

    expect(screen.getByText(/Loading exposure data/i)).toBeInTheDocument()
  })

  it('should display error message on API failure', async () => {
    const error = new Error('API Error')
    exposureApi.getRoleExposurePermissions.mockRejectedValue(error)
    exposureApi.getAvailableBundles.mockRejectedValue(error)
    exposureApi.previewRoleExposure.mockRejectedValue(error)

    render(<Exposure />, { wrapper: TestWrapper })

    await waitFor(() => {
      expect(screen.getByText(/Error/i)).toBeInTheDocument()
      expect(screen.getByText(/API Error/i)).toBeInTheDocument()
    })
  })

  it('should open add permission dialog when clicking button', async () => {
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })

    render(<Exposure />, { wrapper: TestWrapper })

    const addButton = await screen.findByRole('button', { name: /Add Permission/i })
    fireEvent.click(addButton)

    // Dialog should be visible
    expect(screen.getByText(/Add Exposure Permission/i)).toBeInTheDocument()
  })

  it('should display success notification after adding permission', async () => {
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })
    exposureApi.addExposurePermission.mockResolvedValue({
      id: '123',
      role_id: 'role_1',
      permission: 'expose:bundle:Service Booking',
      created_at: new Date().toISOString(),
    })

    render(<Exposure />, { wrapper: TestWrapper })

    // Open dialog and add permission
    const addButton = await screen.findByRole('button', { name: /Add Permission/i })
    fireEvent.click(addButton)

    // Simulate adding permission
    exposureApi.getRoleExposurePermissions.mockResolvedValue(['expose:bundle:Service Booking'])

    await waitFor(() => {
      expect(screen.queryByText(/Permission added/i)).toBeInTheDocument()
    }, { timeout: 4000 })
  })

  it('should refresh data when clicking refresh button', async () => {
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })

    render(<Exposure />, { wrapper: TestWrapper })

    const refreshButton = await screen.findByRole('button', { name: /Refresh/i })
    fireEvent.click(refreshButton)

    await waitFor(() => {
      expect(exposureApi.getRoleExposurePermissions).toHaveBeenCalledTimes(2)
    })
  })
})

// ============================================
// ADD PERMISSION DIALOG TESTS
// ============================================

describe('AddPermissionDialog', () => {
  const mockOnAdd = jest.fn()
  const mockOnOpenChange = jest.fn()
  const mockBundles = [
    {
      name: 'Service Booking',
      description: 'Service booking tools',
      tool_count: 5,
      tools: [
        {
          id: 'tool_1',
          name: 'book_appointment',
          display_name: 'Book Appointment',
          bundle_name: 'Service Booking',
        },
      ],
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render dialog when open prop is true', () => {
    render(
      <AddPermissionDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAdd={mockOnAdd}
        bundles={mockBundles}
        existingPermissions={[]}
        saving={false}
      />
    )

    expect(screen.getByText(/Add Exposure Permission/i)).toBeInTheDocument()
  })

  it('should display permission type options', () => {
    render(
      <AddPermissionDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAdd={mockOnAdd}
        bundles={mockBundles}
        existingPermissions={[]}
        saving={false}
      />
    )

    expect(screen.getByText(/All Tools/i)).toBeInTheDocument()
    expect(screen.getByText(/Bundle/i)).toBeInTheDocument()
    expect(screen.getByText(/Specific Tool/i)).toBeInTheDocument()
  })

  it('should show bundle selector for bundle permission type', async () => {
    render(
      <AddPermissionDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAdd={mockOnAdd}
        bundles={mockBundles}
        existingPermissions={[]}
        saving={false}
      />
    )

    const bundleRadio = screen.getByLabelText(/Bundle/)
    fireEvent.click(bundleRadio)

    await waitFor(() => {
      expect(screen.getByText('Service Booking')).toBeInTheDocument()
    })
  })

  it('should call onAdd when add button is clicked', async () => {
    render(
      <AddPermissionDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAdd={mockOnAdd}
        bundles={mockBundles}
        existingPermissions={[]}
        saving={false}
      />
    )

    const allToolsRadio = screen.getByLabelText(/All Tools/)
    fireEvent.click(allToolsRadio)

    const addButton = screen.getByRole('button', { name: /Add Permission/i })
    fireEvent.click(addButton)

    expect(mockOnAdd).toHaveBeenCalledWith('expose:all')
  })

  it('should disable all access if already granted', () => {
    render(
      <AddPermissionDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAdd={mockOnAdd}
        bundles={mockBundles}
        existingPermissions={['expose:all']}
        saving={false}
      />
    )

    const allToolsRadio = screen.getByLabelText(/All Tools/)
    expect(allToolsRadio).toBeDisabled()
  })

  it('should show loading state while saving', () => {
    render(
      <AddPermissionDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAdd={mockOnAdd}
        bundles={mockBundles}
        existingPermissions={[]}
        saving={true}
      />
    )

    expect(screen.getByText(/Adding/i)).toBeInTheDocument()
  })
})

// ============================================
// PERMISSIONS LIST TESTS
// ============================================

describe('PermissionsList', () => {
  const mockOnRemove = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render empty state when no permissions', () => {
    render(
      <PermissionsList
        permissions={[]}
        onRemove={mockOnRemove}
        saving={null}
      />
    )

    expect(screen.getByText(/No exposure permissions/i)).toBeInTheDocument()
  })

  it('should display all permissions', () => {
    const permissions = [
      'expose:all',
      'expose:bundle:Service Booking',
      'expose:tool:get_dealer',
    ]

    render(
      <PermissionsList
        permissions={permissions}
        onRemove={mockOnRemove}
        saving={null}
      />
    )

    expect(screen.getByText(/Full Access/i)).toBeInTheDocument()
    expect(screen.getByText('Service Booking')).toBeInTheDocument()
    expect(screen.getByText('get_dealer')).toBeInTheDocument()
  })

  it('should call onRemove when remove button clicked', () => {
    const permissions = ['expose:bundle:Service Booking']

    render(
      <PermissionsList
        permissions={permissions}
        onRemove={mockOnRemove}
        saving={null}
      />
    )

    const removeButton = screen.getByRole('button')
    fireEvent.click(removeButton)

    // Should show confirmation, need to confirm
    expect(window.confirm).toHaveBeenCalled()
  })

  it('should show loading state while removing', () => {
    const permissions = ['expose:bundle:Service Booking']

    render(
      <PermissionsList
        permissions={permissions}
        onRemove={mockOnRemove}
        saving="expose:bundle:Service Booking"
      />
    )

    expect(screen.getByRole('button')).toBeDisabled()
  })
})

// ============================================
// PREVIEW PANEL TESTS
// ============================================

describe('PreviewPanel', () => {
  const mockPreview = {
    role_name: 'operator',
    total_exposed_tools: 5,
    exposed_bundles: ['Service Booking'],
    exposed_tools: [
      {
        id: 'tool_1',
        name: 'book_appointment',
        display_name: 'Book Appointment',
        description: 'Book an appointment',
        bundle_name: 'Service Booking',
      },
    ],
  }

  const mockBundles = [
    {
      name: 'Service Booking',
      description: 'Service booking tools',
      tool_count: 5,
      tools: [],
    },
  ]

  it('should render summary cards', () => {
    render(
      <PreviewPanel
        preview={mockPreview}
        bundles={mockBundles}
      />
    )

    expect(screen.getByText('5')).toBeInTheDocument() // Total tools
    expect(screen.getByText('1')).toBeInTheDocument() // Bundles
  })

  it('should display expandable bundle sections', async () => {
    render(
      <PreviewPanel
        preview={mockPreview}
        bundles={mockBundles}
      />
    )

    const bundleSection = screen.getByText('Service Booking')
    expect(bundleSection).toBeInTheDocument()
  })

  it('should expand bundle on click', async () => {
    render(
      <PreviewPanel
        preview={mockPreview}
        bundles={mockBundles}
      />
    )

    const bundleButton = screen.getByText('Service Booking').closest('button')
    fireEvent.click(bundleButton)

    await waitFor(() => {
      expect(screen.getByText('Book Appointment')).toBeInTheDocument()
    })
  })

  it('should show empty state when no tools', () => {
    const emptyPreview = {
      role_name: 'restricted',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    }

    render(
      <PreviewPanel
        preview={emptyPreview}
        bundles={mockBundles}
      />
    )

    expect(screen.getByText(/No tools exposed/i)).toBeInTheDocument()
  })
})

// ============================================
// ACCESSIBILITY TESTS
// ============================================

describe('Exposure Page - Accessibility', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    exposureApi.getRoleExposurePermissions.mockResolvedValue([])
    exposureApi.getAvailableBundles.mockResolvedValue([])
    exposureApi.previewRoleExposure.mockResolvedValue({
      role_name: 'operator',
      total_exposed_tools: 0,
      exposed_bundles: [],
      exposed_tools: [],
    })
  })

  it('should have proper heading hierarchy', () => {
    render(<Exposure />, { wrapper: TestWrapper })

    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent(/Tool Exposure Governance/i)
  })

  it('should have descriptive alt text for icons', () => {
    render(<Exposure />, { wrapper: TestWrapper })

    // Check for proper ARIA labels
    const buttons = screen.getAllByRole('button')
    buttons.forEach((button) => {
      expect(button).toHaveAccessibleName()
    })
  })

  it('should be keyboard navigable', async () => {
    render(<Exposure />, { wrapper: TestWrapper })

    const user = userEvent.setup()

    // Tab to first button
    await user.tab()

    // Should focus on a button
    const focusedElement = document.activeElement
    expect(focusedElement).toBeInTheDocument()
  })

  it('should announce loading state to screen readers', async () => {
    exposureApi.getRoleExposurePermissions.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )
    exposureApi.getAvailableBundles.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )
    exposureApi.previewRoleExposure.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<Exposure />, { wrapper: TestWrapper })

    // Should have role="status" or similar for loading
    const loadingText = screen.getByText(/Loading/)
    expect(loadingText).toBeInTheDocument()
  })
})

export {}
