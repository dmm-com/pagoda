---
title: Plugin System Architecture Diagrams
weight: 1
---

## System Architecture Overview

### 3-Layer Architecture Flow

```mermaid
graph TB
    subgraph "Layer 1: Core Framework (pagoda-plugin-sdk)"
        PC[pagoda-plugin-sdk Package]
        PI[Plugin Interfaces]
        PB[Base Plugin Class]
        CH[Common Hooks]
        AM[API Mixins]
    end

    subgraph "Layer 2: External Plugin"
        EP[External Plugin Package]
        PL[Plugin Logic]
        API[API Endpoints]
        HH[Hook Handlers]
        DJ[Django App Config]
    end

    subgraph "Layer 3: Pagoda Host Application"
        AB[Auth Bridge]
        DB[Data Bridge]
        HB[Hook Bridge]
        BM[Bridge Manager]
        UI[URL Integration]
        AS[Pagoda Settings]
    end

    PC --> EP
    PI --> EP
    PB --> EP
    CH --> EP
    AM --> EP

    EP --> AB
    EP --> DB
    EP --> HB
    EP --> BM
    EP --> UI
    EP --> AS

    style PC fill:#e1f5fe
    style EP fill:#f3e5f5
    style AB fill:#e8f5e8
```

### Plugin Discovery & Registration Flow

```mermaid
sequenceDiagram
    participant ENV as Environment
    participant AI as Pagoda Init
    participant PD as Plugin Discovery
    participant PR as Plugin Registry
    participant BM as Bridge Manager
    participant DU as Django URLs

    ENV->>AI: ENABLED_PLUGINS=hello-world
    AI->>PD: Start plugin discovery

    par External Plugin Discovery
        PD->>PD: pkg_resources.iter_entry_points('pagoda.plugins')
        PD->>PR: Register external plugins
    and Example Plugin Discovery
        PD->>PD: Scan plugin/examples/ directory
        PD->>PR: Register example plugins
    end

    PR->>BM: Initialize bridge manager
    BM->>BM: Setup Auth/Data/Hook bridges
    PR->>PR: Register plugin hooks
    PR->>DU: Integrate URL patterns
    DU->>AI: Plugin endpoints available

    Note over ENV,AI: Plugin system ready
```

### Hook System Architecture

```mermaid
graph LR
    subgraph "Hook Registration"
        PC[pagoda-plugin-sdk<br/>COMMON_HOOKS]
        AH[Pagoda Specific<br/>Hooks]
        HR[Hook Registry<br/>42 total hooks]
    end

    subgraph "Plugin Implementation"
        PH[Plugin Hook<br/>Handlers]
        EP[Entry Points<br/>Configuration]
    end

    subgraph "Execution Flow"
        DS[Django Signals]
        HE[Hook Executor]
        CB[Plugin Callbacks]
        ER[Error Recovery]
    end

    PC --> HR
    AH --> HR
    HR --> HE

    EP --> PH
    PH --> CB

    DS --> HE
    HE --> CB
    CB --> ER

    style PC fill:#e1f5fe
    style PH fill:#f3e5f5
    style HE fill:#e8f5e8
```

### API Integration Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CL[Client Request]
        AUTH[Authentication]
    end

    subgraph "Pagoda Core"
        URLS[Django URLs]
        MW[Middleware]
        APIV2[API v2 Router]
    end

    subgraph "Plugin Layer"
        PU[Plugin URLs]
        PAM[Plugin API Mixin]
        PV[Plugin Views]
        PL[Plugin Logic]
    end

    subgraph "Bridge Layer"
        BM[Bridge Manager]
        AB[Auth Bridge]
        DB[Data Bridge]
        HB[Hook Bridge]
    end

    subgraph "Pagoda Backend"
        MODELS[Django Models]
        PERMS[Permissions]
        HOOKS[Hook System]
    end

    CL --> AUTH
    AUTH --> MW
    MW --> URLS
    URLS --> APIV2
    APIV2 --> PU
    PU --> PAM
    PAM --> PV
    PV --> PL

    PL --> BM
    BM --> AB
    BM --> DB
    BM --> HB

    AB --> PERMS
    DB --> MODELS
    HB --> HOOKS

    style CL fill:#ffebee
    style PL fill:#f3e5f5
    style BM fill:#e8f5e8
    style MODELS fill:#e3f2fd
```

## Plugin Development Lifecycle

### Development Phase Architecture

```mermaid
graph TD
    subgraph "Development Environment"
        DEV[Developer Machine]
        PC[pagoda-plugin-sdk install]
        PE[Plugin Examples]
        IDE[IDE/Editor]
    end

    subgraph "Local Testing"
        LS[Local Server]
        PI[Plugin Install]
        IT[Integration Tests]
        UT[Unit Tests]
    end

    subgraph "Build & Package"
        BP[Build Process]
        PKG[Package Creation]
        TEST[Test Distribution]
        DOC[Documentation]
    end

    subgraph "Distribution"
        PYPI[PyPI Publication]
        GHR[GitHub Releases]
        PRIV[Private Registry]
    end

    DEV --> PC
    PC --> PE
    PE --> IDE
    IDE --> LS

    LS --> PI
    PI --> IT
    IT --> UT
    UT --> BP

    BP --> PKG
    PKG --> TEST
    TEST --> DOC
    DOC --> PYPI
    DOC --> GHR
    DOC --> PRIV

    style DEV fill:#e1f5fe
    style BP fill:#f3e5f5
    style PYPI fill:#e8f5e8
```

### Runtime Architecture

```mermaid
graph LR
    subgraph "Production Environment"
        PROD[Production Server]
        ENV[Environment Variables]
        DEPS[Dependencies]
    end

    subgraph "Pagoda Instance"
        DJANGO[Django Application]
        SETTINGS[Settings Integration]
        INSTALLED[Installed Apps]
    end

    subgraph "Plugin Runtime"
        PREG[Plugin Registry]
        PINT[Plugin Integration]
        APIS[API Endpoints]
        HOOKS[Active Hooks]
    end

    subgraph "Monitoring"
        LOGS[Log Monitoring]
        PERF[Performance Metrics]
        ERRORS[Error Tracking]
    end

    PROD --> ENV
    ENV --> DJANGO
    DJANGO --> SETTINGS
    SETTINGS --> INSTALLED
    INSTALLED --> PREG

    PREG --> PINT
    PINT --> APIS
    PINT --> HOOKS

    APIS --> LOGS
    HOOKS --> LOGS
    LOGS --> PERF
    LOGS --> ERRORS

    style PROD fill:#ffebee
    style PREG fill:#f3e5f5
    style LOGS fill:#e8f5e8
```

## Data Flow Diagrams

### Plugin API Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant Pagoda as Pagoda Server
    participant PluginAPI as Plugin API View
    participant Bridge as Bridge Manager
    participant DB as Database

    C->>Pagoda: GET /api/v2/plugins/my-plugin/hello/
    Pagoda->>Pagoda: Authentication check
    Pagoda->>PluginAPI: Route to plugin endpoint
    PluginAPI->>PluginAPI: Plugin logic execution
    PluginAPI->>Bridge: Request data via bridge
    Bridge->>DB: Execute database query
    DB-->>Bridge: Return data
    Bridge-->>PluginAPI: Formatted data
    PluginAPI-->>Pagoda: API response
    Pagoda-->>C: JSON response

    Note over C,DB: Complete plugin API request flow
```

### Plugin Hook Execution Flow

```mermaid
sequenceDiagram
    participant User as User Action
    participant Pagoda as Pagoda Core
    participant Django as Django Signal
    participant HookBridge as Hook Bridge
    participant Plugin as Plugin Handler

    User->>Pagoda: Create Entry
    Pagoda->>Django: post_save signal
    Django->>HookBridge: entry.after_create hook
    HookBridge->>HookBridge: Find registered callbacks

    loop For each plugin callback
        HookBridge->>Plugin: Execute plugin hook
        Plugin->>Plugin: Custom logic
        Plugin-->>HookBridge: Return result
    end

    HookBridge-->>Django: All results
    Django-->>Pagoda: Hook execution complete
    Pagoda-->>User: Entry created successfully

    Note over User,Plugin: Plugin hook execution on entry creation
```

## Error Handling & Recovery

### Plugin Error Isolation

```mermaid
graph TD
    subgraph "Error Sources"
        PE[Plugin Error]
        DE[Discovery Error]
        RE[Registration Error]
        HE[Hook Error]
    end

    subgraph "Error Handling"
        EH[Error Handler]
        LOG[Error Logging]
        ISO[Error Isolation]
        REC[Recovery Logic]
    end

    subgraph "System Response"
        CONT[Continue Operation]
        ALERT[Admin Alert]
        SKIP[Skip Plugin]
        FALLBACK[Fallback Mode]
    end

    PE --> EH
    DE --> EH
    RE --> EH
    HE --> EH

    EH --> LOG
    EH --> ISO
    EH --> REC

    LOG --> ALERT
    ISO --> SKIP
    ISO --> CONT
    REC --> FALLBACK

    style PE fill:#ffebee
    style EH fill:#fff3e0
    style CONT fill:#e8f5e8
```

### Plugin System Health Check

```mermaid
graph LR
    subgraph "Health Monitoring"
        HC[Health Check]
        PS[Plugin Status]
        EP[Endpoint Status]
        HS[Hook Status]
    end

    subgraph "Metrics Collection"
        PM[Performance Metrics]
        EM[Error Metrics]
        UM[Usage Metrics]
    end

    subgraph "Alerting"
        TH[Thresholds]
        AL[Alerts]
        NOT[Notifications]
    end

    HC --> PS
    HC --> EP
    HC --> HS

    PS --> PM
    EP --> PM
    HS --> PM

    PM --> EM
    PM --> UM
    EM --> TH
    UM --> TH

    TH --> AL
    AL --> NOT

    style HC fill:#e1f5fe
    style PM fill:#f3e5f5
    style AL fill:#ffebee
```

## Security Architecture

### Plugin Security Boundaries

```mermaid
graph TB
    subgraph "Security Layers"
        AUTH[Authentication Layer]
        AUTHZ[Authorization Layer]
        VALID[Input Validation]
        SAND[Plugin Sandboxing]
    end

    subgraph "Plugin Constraints"
        API[API Limitations]
        PERM[Permission Checking]
        RATE[Rate Limiting]
        AUDIT[Audit Logging]
    end

    subgraph "Core Protection"
        ISOL[Core Isolation]
        INTER[Interface Controls]
        BRIDGE[Bridge Security]
    end

    AUTH --> API
    AUTHZ --> PERM
    VALID --> RATE
    SAND --> AUDIT

    API --> ISOL
    PERM --> INTER
    RATE --> BRIDGE
    AUDIT --> BRIDGE

    style AUTH fill:#ffebee
    style SAND fill:#fff3e0
    style ISOL fill:#e8f5e8
```

Through this 3-layer architecture design, Pagoda provides a completely independent plugin ecosystem, realizing a secure and extensible platform. Plugin developers can provide unique value while accessing Pagoda's core functionality through standardized interfaces.