# Observability Guide

**Document Version**: 2.1  
**Last Updated**: February 1, 2026  
**Classification**: Internal

---

## 1. Overview

This document describes the observability strategy including logging, metrics, tracing, dashboards, and alerting for the MSIL MCP Platform.

> **🔒 PII Protection**: PII (Aadhaar, PAN, mobile, email) MUST NEVER appear in logs, traces, metrics labels, or dashboard displays. All logging code must use correlation IDs and business identifiers only. See Section 3.3 for mandatory masking rules.

---

## 2. Observability Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OBSERVABILITY ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           APPLICATION LAYER                                     │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                   │   │
│   │   │  Structured   │   │   Prometheus  │   │  OpenTelemetry│                   │   │
│   │   │    Logs       │   │    Metrics    │   │    Traces     │                   │   │
│   │   │               │   │               │   │               │                   │   │
│   │   │ JSON format   │   │ /metrics      │   │ W3C Trace     │                   │   │
│   │   │ Correlation   │   │ endpoint      │   │ Context       │                   │   │
│   │   │ ID in every   │   │               │   │               │                   │   │
│   │   │ log line      │   │               │   │               │                   │   │
│   │   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘                   │   │
│   │           │                   │                   │                            │   │
│   └───────────┼───────────────────┼───────────────────┼────────────────────────────┘   │
│               │                   │                   │                                │
│               ▼                   ▼                   ▼                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           COLLECTION LAYER                                      │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                   │   │
│   │   │   Fluent Bit  │   │  CloudWatch   │   │ AWS X-Ray     │                   │   │
│   │   │   (DaemonSet) │   │    Agent      │   │   Daemon      │                   │   │
│   │   │               │   │               │   │               │                   │   │
│   │   │ • Tail logs   │   │ • Scrape      │   │ • Receive     │                   │   │
│   │   │ • Parse JSON  │   │   Prometheus  │   │   segments    │                   │   │
│   │   │ • Add K8s     │   │ • Publish to  │   │ • Batch &     │                   │   │
│   │   │   metadata    │   │   CloudWatch  │   │   forward     │                   │   │
│   │   │ • Batch send  │   │   Metrics     │   │               │                   │   │
│   │   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘                   │   │
│   │           │                   │                   │                            │   │
│   └───────────┼───────────────────┼───────────────────┼────────────────────────────┘   │
│               │                   │                   │                                │
│               ▼                   ▼                   ▼                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           AWS OBSERVABILITY                                     │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                   │   │
│   │   │  CloudWatch   │   │  CloudWatch   │   │   AWS X-Ray   │                   │   │
│   │   │    Logs       │   │   Metrics     │   │               │                   │   │
│   │   │               │   │               │   │               │                   │   │
│   │   │ • Log Groups  │   │ • Custom      │   │ • Service Map │                   │   │
│   │   │ • Insights    │   │   Namespace   │   │ • Traces      │                   │   │
│   │   │ • Subscript.  │   │ • Dashboards  │   │ • Analytics   │                   │   │
│   │   │               │   │ • Alarms      │   │               │                   │   │
│   │   └───────────────┘   └───────────────┘   └───────────────┘                   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Logging

### 3.1 Log Format

```json
{
  "timestamp": "2026-01-31T10:30:00.123Z",
  "level": "INFO",
  "logger": "mcp.tool_executor",
  "message": "Tool execution completed",
  "service": "mcp-server",
  "version": "2.0.0",
  "environment": "production",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "trace_id": "1234567890abcdef1234567890abcdef",
  "span_id": "abcdef1234567890",
  "user_id": "user@msil.com",
  "context": {
    "tool_name": "get_dealer_enquiries",
    "dealer_id": "DL123456",
    "duration_ms": 156,
    "status": "success"
  },
  "kubernetes": {
    "namespace": "mcp-production",
    "pod_name": "mcp-server-abc123",
    "node_name": "ip-10-0-1-100"
  }
}
```

### 3.2 Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| **ERROR** | Errors requiring attention | Tool execution failed, Auth failed |
| **WARNING** | Potential issues | Rate limit approaching, Retry attempt |
| **INFO** | Normal operations | Tool executed, User logged in |
| **DEBUG** | Detailed debugging | Request details, Cache hits |

### 3.3 Sensitive Data Handling

> **⚠️ CRITICAL REQUIREMENT**: PII MUST NEVER appear in logs, traces, metrics, or dashboards.

**Prohibited Data in Observability:**

| Data Type | Pattern | Replacement |
|-----------|---------|-------------|
| Aadhaar | 12-digit number | `[AADHAAR_REDACTED]` |
| PAN | ABCDE1234F format | `[PAN_REDACTED]` |
| Mobile | 10-digit number | `[MOBILE_REDACTED]` |
| Email | *@*.* format | `[EMAIL_REDACTED]` |
| Customer Name | Free text | Use `customer_id` only |

**Mandatory PII Masking Filter:**

```python
# Logger configuration with PII masking
import re
import logging

class PIIMaskingFilter(logging.Filter):
    """
    Mask PII in log messages.
    
    CRITICAL: This filter is MANDATORY for all loggers.
    Logs containing unmasked PII will fail security audits.
    """
    
    PATTERNS = [
        (r'\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b', '[AADHAAR_REDACTED]'),  # Aadhaar
        (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '[PAN_REDACTED]'),                      # PAN
        (r'\b(?:91)?[6-9][0-9]{9}\b', '[MOBILE_REDACTED]'),                    # Mobile
        (r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b', '[EMAIL_REDACTED]'),                 # Email
    ]
    
    def filter(self, record):
        message = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        record.args = ()  # Clear args to prevent re-formatting
        return True

# Apply filter to all loggers
logging.getLogger().addFilter(PIIMaskingFilter())
```

**Correct Logging Practices:**

```python
# ✅ CORRECT: Use correlation IDs and business identifiers
logger.info("Tool executed", extra={
    "correlation_id": correlation_id,
    "tool_name": tool_name,
    "dealer_code": dealer_code,      # Business ID
    "enquiry_id": enquiry_id,        # System ID
    "duration_ms": duration_ms
})

# ❌ WRONG: NEVER log PII
# logger.info(f"Customer {customer_name} ({mobile}) created enquiry")
# logger.debug(f"Processing request for {email}")
```

**Trace Span Attribute Rules:**

```python
# ✅ CORRECT: Safe span attributes
span.set_attribute("user.id", user_id)           # Internal ID
span.set_attribute("dealer.code", dealer_code)   # Business code
span.set_attribute("tool.name", tool_name)

# ❌ WRONG: Never include PII in traces
# span.set_attribute("user.email", email)
# span.set_attribute("customer.phone", phone)
```

### 3.4 CloudWatch Log Groups

| Log Group | Source | Retention |
|-----------|--------|-----------|
| `/mcp/server` | MCP Server application | 30 days |
| `/mcp/admin-ui` | Admin Portal access logs | 30 days |
| `/mcp/chat-ui` | Chat UI access logs | 30 days |
| `/mcp/audit` | Security audit events | 7 years |
| `/mcp/opa` | Policy decisions | 30 days |

---

## 4. Metrics

### 4.1 Key Metrics

```python
# Prometheus metrics definition
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'mcp_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'mcp_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[.01, .05, .1, .25, .5, 1, 2.5, 5, 10]
)

# Tool metrics
TOOL_EXECUTIONS = Counter(
    'mcp_tool_executions_total',
    'Total tool executions',
    ['tool_name', 'risk_level', 'status']
)

TOOL_LATENCY = Histogram(
    'mcp_tool_execution_seconds',
    'Tool execution latency',
    ['tool_name'],
    buckets=[.1, .25, .5, 1, 2.5, 5, 10, 30]
)

# Security metrics
AUTH_FAILURES = Counter(
    'mcp_auth_failures_total',
    'Authentication failures',
    ['reason']
)

POLICY_DECISIONS = Counter(
    'mcp_policy_decisions_total',
    'Policy decisions',
    ['action', 'result']
)

# System metrics
ACTIVE_CONNECTIONS = Gauge(
    'mcp_active_connections',
    'Current active database connections'
)

CIRCUIT_BREAKER_STATE = Gauge(
    'mcp_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 0.5=half-open)',
    ['service']
)
```

### 4.2 CloudWatch Custom Metrics

| Metric | Namespace | Dimensions | Unit |
|--------|-----------|------------|------|
| `RequestCount` | MCP/API | Endpoint, Method | Count |
| `RequestLatencyP99` | MCP/API | Endpoint | Milliseconds |
| `ErrorRate` | MCP/API | Endpoint | Percent |
| `ToolExecutions` | MCP/Tools | ToolName, RiskLevel | Count |
| `ToolLatency` | MCP/Tools | ToolName | Milliseconds |
| `AuthFailures` | MCP/Security | Reason | Count |
| `PolicyDenials` | MCP/Security | Action | Count |
| `CacheHitRate` | MCP/Cache | CacheType | Percent |

---

## 5. Distributed Tracing

### 5.1 OpenTelemetry Configuration

```python
# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def setup_tracing(app):
    """Configure OpenTelemetry tracing."""
    
    # Set up provider
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": "mcp-server",
            "service.version": "2.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "production")
        })
    )
    
    # X-Ray exporter
    exporter = OTLPSpanExporter(
        endpoint="localhost:4317"  # AWS Distro for OpenTelemetry Collector
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    
    # Auto-instrumentation
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
```

### 5.2 Custom Spans

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def execute_tool(tool_name: str, parameters: dict):
    """Execute tool with tracing."""
    
    with tracer.start_as_current_span(
        "tool_execution",
        attributes={
            "tool.name": tool_name,
            "tool.risk_level": tool.risk_level,
        }
    ) as span:
        # Validate parameters
        with tracer.start_as_current_span("validate_parameters"):
            await validate_parameters(tool, parameters)
        
        # Check authorization
        with tracer.start_as_current_span("check_authorization"):
            await check_authorization(user, tool)
        
        # Execute backend call
        with tracer.start_as_current_span(
            "backend_call",
            attributes={"http.url": tool.api_endpoint}
        ):
            result = await call_backend(tool, parameters)
        
        span.set_attribute("tool.result_size", len(str(result)))
        return result
```

### 5.3 Trace Context Propagation

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              TRACE CONTEXT FLOW                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   LLM Client                MCP Server              APIM              Backend           │
│       │                         │                    │                   │              │
│       │ traceparent:00-abc...   │                    │                   │              │
│       │ X-Correlation-ID:xyz    │                    │                   │              │
│       │─────────────────────────▶│                    │                   │              │
│       │                         │                    │                   │              │
│       │                         │ [Span: mcp_request]│                   │              │
│       │                         │ traceparent:00-abc │                   │              │
│       │                         │ X-Correlation-ID:xy│                   │              │
│       │                         │────────────────────▶│                   │              │
│       │                         │                    │                   │              │
│       │                         │                    │ [Span: apim_route]│              │
│       │                         │                    │ traceparent:00-abc│              │
│       │                         │                    │───────────────────▶│              │
│       │                         │                    │                   │              │
│       │                         │                    │                   │ [Span: api]  │
│       │                         │                    │◀──────────────────│              │
│       │                         │                    │                   │              │
│       │                         │◀───────────────────│                   │              │
│       │                         │                    │                   │              │
│       │◀────────────────────────│                    │                   │              │
│       │                         │                    │                   │              │
│                                                                                         │
│   All spans share: trace_id=abc..., correlation_id=xyz                                  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Dashboards

### 6.1 CloudWatch Dashboard - API Performance

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Request Rate",
        "metrics": [
          ["MCP/API", "RequestCount", {"stat": "Sum", "period": 60}]
        ],
        "view": "timeSeries"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Latency Percentiles",
        "metrics": [
          ["MCP/API", "RequestLatency", {"stat": "p50"}],
          [".", ".", {"stat": "p95"}],
          [".", ".", {"stat": "p99"}]
        ],
        "view": "timeSeries"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Error Rate",
        "metrics": [
          ["MCP/API", "ErrorRate", {"stat": "Average"}]
        ],
        "view": "timeSeries",
        "annotations": {
          "horizontal": [{"value": 1, "label": "1% threshold"}]
        }
      }
    }
  ]
}
```

### 6.2 Dashboard Views

| Dashboard | Purpose | Key Widgets |
|-----------|---------|-------------|
| **API Overview** | Overall API health | Request rate, Latency, Errors |
| **Tool Analytics** | Tool usage patterns | Executions by tool, Top tools, Error rates |
| **Security** | Security monitoring | Auth failures, Policy denials, Rate limits |
| **Infrastructure** | Resource utilization | CPU, Memory, DB connections |

---

## 7. Alerting

### 7.1 Alert Rules

```yaml
# CloudWatch Alarm definitions

# High Error Rate
HighErrorRateAlarm:
  MetricName: ErrorRate
  Namespace: MCP/API
  Statistic: Average
  Period: 300
  EvaluationPeriods: 2
  Threshold: 5
  ComparisonOperator: GreaterThanThreshold
  TreatMissingData: notBreaching
  AlarmActions:
    - !Ref PagerDutySNS

# High Latency
HighLatencyAlarm:
  MetricName: RequestLatencyP99
  Namespace: MCP/API
  Statistic: Average
  Period: 300
  EvaluationPeriods: 3
  Threshold: 2000  # 2 seconds
  ComparisonOperator: GreaterThanThreshold
  AlarmActions:
    - !Ref SlackSNS

# Authentication Failures Spike
AuthFailuresSpikeAlarm:
  MetricName: AuthFailures
  Namespace: MCP/Security
  Statistic: Sum
  Period: 60
  EvaluationPeriods: 5
  Threshold: 100
  ComparisonOperator: GreaterThanThreshold
  AlarmActions:
    - !Ref SecuritySNS
    - !Ref PagerDutySNS

# Circuit Breaker Open
CircuitBreakerOpenAlarm:
  MetricName: CircuitBreakerState
  Namespace: MCP/Resilience
  Dimensions:
    - Name: Service
      Value: APIM
  Statistic: Maximum
  Period: 60
  EvaluationPeriods: 1
  Threshold: 1
  ComparisonOperator: GreaterThanOrEqualToThreshold
  AlarmActions:
    - !Ref PagerDutySNS
```

### 7.2 Alert Routing

| Severity | Channel | Response Time |
|----------|---------|---------------|
| **Critical** | PagerDuty → On-call | 15 minutes |
| **High** | Slack #mcp-alerts + Email | 1 hour |
| **Medium** | Slack #mcp-alerts | 4 hours |
| **Low** | Email digest | Next business day |

### 7.3 Alert Escalation

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ALERT ESCALATION                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Alert Triggered                                                                       │
│        │                                                                                │
│        ▼                                                                                │
│   ┌───────────────────┐                                                                 │
│   │ L1: On-Call SRE   │ ◀── 15 min response                                            │
│   └─────────┬─────────┘                                                                 │
│             │ Not resolved in 30 min                                                    │
│             ▼                                                                           │
│   ┌───────────────────┐                                                                 │
│   │ L2: Platform Team │ ◀── Auto-escalate + L1                                         │
│   └─────────┬─────────┘                                                                 │
│             │ Not resolved in 1 hour                                                    │
│             ▼                                                                           │
│   ┌───────────────────┐                                                                 │
│   │ L3: Engineering   │ ◀── Manager notification                                       │
│   │     Manager       │                                                                 │
│   └───────────────────┘                                                                 │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Log Analysis Queries

### 8.1 CloudWatch Insights Queries

```sql
-- Error analysis
fields @timestamp, @message, correlation_id, user_id, context.tool_name
| filter level = "ERROR"
| sort @timestamp desc
| limit 100

-- Tool execution latency
fields @timestamp, context.tool_name, context.duration_ms
| filter message = "Tool execution completed"
| stats avg(context.duration_ms) as avg_latency, 
        percentile(context.duration_ms, 99) as p99_latency 
  by context.tool_name
| sort p99_latency desc

-- Authentication failures by reason
fields @timestamp, user_id, context.reason
| filter message like /auth.*fail/i
| stats count() as failure_count by context.reason
| sort failure_count desc

-- User activity
fields @timestamp, user_id, context.tool_name, context.status
| filter user_id = "user@msil.com"
| sort @timestamp desc
| limit 50

-- Security events
fields @timestamp, user_id, message, context
| filter level = "WARNING" and logger like /security/
| sort @timestamp desc
```

---

## 9. SLIs and SLOs

### 9.1 Service Level Indicators

| SLI | Definition | Measurement |
|-----|------------|-------------|
| **Availability** | Successful requests / Total requests | CloudWatch metrics |
| **Latency** | Time to first byte (P99) | X-Ray traces |
| **Error Rate** | 5xx responses / Total responses | ALB metrics |
| **Throughput** | Requests per second | CloudWatch metrics |

### 9.2 Service Level Objectives

| Service | SLO Target | Error Budget |
|---------|------------|--------------|
| API Availability | 99.9% | 43.8 min/month |
| API Latency (P99) | < 1 second | N/A |
| Tool Execution Success | 99.5% | 3.65 hours/month |
| Auth Success Rate | 99.99% | 4.4 min/month |

---

*Document Classification: Internal | Last Review: January 31, 2026*
