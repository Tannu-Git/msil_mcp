# Architecture Documentation

This folder contains all architecture documentation for the MSIL MCP Platform.

## Documents

| Document | Description |
|----------|-------------|
| [01-high-level-architecture.md](./01-high-level-architecture.md) | Logical view and system topology |
| [02-low-level-architecture.md](./02-low-level-architecture.md) | Detailed component design |
| [03-security-architecture.md](./03-security-architecture.md) | Security controls and flows (includes Exposure Governance) |
| [04-deployment-architecture.md](./04-deployment-architecture.md) | Infrastructure and CI/CD |
| [05-integration-architecture.md](./05-integration-architecture.md) | API Manager integration |

## Architecture Principles

1. **Security by Design** - Security controls at every layer
2. **API-First** - All functionality exposed via APIs
3. **Cloud-Native** - Designed for containerized deployment
4. **Observable** - Full visibility into system behavior
5. **Resilient** - Fault-tolerant with graceful degradation
6. **Scalable** - Horizontal scaling capabilities
7. **Governed** - Policy-driven access control
8. **Visible by Need** - Exposure Governance limits tool visibility by role
