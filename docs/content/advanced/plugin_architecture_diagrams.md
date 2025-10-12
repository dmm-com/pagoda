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
        MI[Model Injection]
        PI_SYS[Plugin Integration]
        UI[URL Integration]
        AS[Pagoda Settings]
        DM[Django Models]
    end

    PC --> EP
    PI --> EP
    PB --> EP
    CH --> EP
    AM --> EP

    EP --> MI
    EP --> PI_SYS
    EP --> UI
    EP --> AS
    DM --> MI
    MI --> PC

    style PC fill:#e1f5fe
    style EP fill:#f3e5f5
    style MI fill:#e8f5e8
```

### Plugin Discovery & Registration Flow

```mermaid
sequenceDiagram
    participant ENV as Environment
    participant AI as Pagoda Init
    participant PD as Plugin Discovery
    participant PR as Plugin Registry
    participant MI as Model Injection
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

    PR->>MI: Initialize model injection
    MI->>MI: Inject Entity, Entry, User models
    PR->>PR: Register plugin hooks
    PR->>DU: Integrate URL patterns
    DU->>AI: Plugin endpoints available

    Note over ENV,AI: Plugin system ready
```

### Hook System Architecture

```mermaid
graph LR
    subgraph "Hook Registration"
        PC[pagoda-plugin-sdk<br/>17 Standard Hooks]
        AH[Legacy Aliases<br/>HOOK_ALIASES]
        HR[Hook Manager<br/>Registry]
    end

    subgraph "Plugin Implementation"
        PH[Plugin Hook<br/>Handlers]
        DEC[Decorators<br/>@entry_hook, etc.]
    end

    subgraph "Execution Flow"
        DS[Django Signals]
        HE[Hook Executor]
        CB[Plugin Callbacks]
        ER[Error Isolation]
    end

    PC --> HR
    AH --> HR
    HR --> HE

    DEC --> PH
    PH --> CB

    DS --> HE
    HE --> CB
    CB --> ER

    style PC fill:#e1f5fe
    style PH fill:#f3e5f5
    style HE fill:#e8f5e8
```

### Hook Manager Detailed Architecture

```mermaid
graph TB
    subgraph "Hook Registration Phase"
        PLUGIN[Plugin Class]
        DECO[Decorator Metadata]
        SCAN[__init_subclass__<br/>Auto-scan]
        META[_hook_handlers<br/>List]
    end

    subgraph "Hook Manager"
        REG[register_hook]
        HOOKS[_hooks Dict<br/>hook_name -> handlers]
        SORT[Priority Sorting]
    end

    subgraph "Hook Execution Phase"
        EXEC[execute_hook]
        NORM[Normalize Name<br/>Handle Aliases]
        FILT[Entity Filter]
        PRIOR[Priority Order]
        CALL[Call Handlers]
        ERR[Error Handling]
    end

    PLUGIN --> DECO
    DECO --> SCAN
    SCAN --> META

    META --> REG
    REG --> HOOKS
    HOOKS --> SORT

    EXEC --> NORM
    NORM --> FILT
    FILT --> PRIOR
    PRIOR --> CALL
    CALL --> ERR

    style PLUGIN fill:#e1f5fe
    style HOOKS fill:#f3e5f5
    style EXEC fill:#fff3e0
    style ERR fill:#ffebee
```

### Hook Execution Flow with Entity Filtering

```mermaid
sequenceDiagram
    participant App as Application
    participant HM as Hook Manager
    participant P1 as Plugin A<br/>(entity="customer")
    participant P2 as Plugin B<br/>(all entities)
    participant P3 as Plugin C<br/>(entity="customer")

    App->>HM: execute_hook("entry.after_create", entity_name="customer")
    HM->>HM: Normalize hook name
    HM->>HM: Get handlers for "entry.after_create"
    HM->>HM: Filter by entity="customer"

    Note over HM: Found 3 handlers:<br/>Plugin A (priority 50, entity="customer")<br/>Plugin B (priority 100, all entities)<br/>Plugin C (priority 150, entity="customer")

    HM->>P1: Execute (priority 50)
    P1-->>HM: Success

    HM->>P2: Execute (priority 100)
    P2-->>HM: Success

    HM->>P3: Execute (priority 150)
    P3-->>HM: Success

    HM-->>App: All handlers executed

    Note over App,HM: If entity_name="product",<br/>only Plugin B would be called
```

### Decorator-Based Hook Registration

```mermaid
graph TB
    subgraph "Plugin Definition"
        CLASS[Plugin Class<br/>MyPlugin]
        DEC1[@entry_hook<br/>"after_create"]
        DEC2[@entity_hook<br/>"after_create"]
        DEC3[@validation_hook]
        DEC4[@get_attrs_hook<br/>"entry"]
        METHOD1[handler method 1]
        METHOD2[handler method 2]
        METHOD3[handler method 3]
        METHOD4[handler method 4]
    end

    subgraph "Metaclass Processing"
        INIT[__init_subclass__]
        SCAN[Scan class methods]
        CHECK[Check for _hook_metadata]
        COLLECT[Collect to _hook_handlers]
    end

    subgraph "Registration"
        INST[Plugin Instance]
        REG[registry.register]
        HOOK_REG[Register each hook]
        HM[Hook Manager]
    end

    CLASS --> DEC1 --> METHOD1
    CLASS --> DEC2 --> METHOD2
    CLASS --> DEC3 --> METHOD3
    CLASS --> DEC4 --> METHOD4

    METHOD1 --> INIT
    METHOD2 --> INIT
    METHOD3 --> INIT
    METHOD4 --> INIT

    INIT --> SCAN
    SCAN --> CHECK
    CHECK --> COLLECT

    COLLECT --> INST
    INST --> REG
    REG --> HOOK_REG
    HOOK_REG --> HM

    style CLASS fill:#e1f5fe
    style INIT fill:#f3e5f5
    style HM fill:#e8f5e8
```

### Priority-Based Execution Order

```mermaid
graph LR
    subgraph "Hook: entry.after_create"
        H1[Plugin A<br/>priority: 50<br/>entity: customer]
        H2[Plugin B<br/>priority: 75<br/>entity: *]
        H3[Plugin C<br/>priority: 100<br/>entity: customer]
        H4[Plugin D<br/>priority: 100<br/>entity: *]
        H5[Plugin E<br/>priority: 150<br/>entity: customer]
    end

    subgraph "Execution Sequence"
        E1[1st: Plugin A<br/>priority 50]
        E2[2nd: Plugin B<br/>priority 75]
        E3[3rd: Plugin C<br/>priority 100]
        E4[4th: Plugin D<br/>priority 100]
        E5[5th: Plugin E<br/>priority 150]
    end

    H1 -.lower priority<br/>executes first.-> E1
    H2 --> E2
    H3 --> E3
    H4 --> E4
    H5 -.higher priority<br/>executes last.-> E5

    style H1 fill:#c8e6c9
    style H2 fill:#c8e6c9
    style H3 fill:#fff9c4
    style H4 fill:#fff9c4
    style H5 fill:#ffcdd2
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

    subgraph "Model Access Layer"
        MI[Model Injection]
        SDK_MODELS[SDK Models]
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

    PL --> SDK_MODELS
    SDK_MODELS --> MI
    MI --> MODELS

    PV --> PERMS
    PV --> HOOKS

    style CL fill:#ffebee
    style PL fill:#f3e5f5
    style MI fill:#e8f5e8
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
    participant SDK_MODELS as SDK Models
    participant DB as Database

    C->>Pagoda: GET /api/v2/plugins/my-plugin/entities/
    Pagoda->>Pagoda: Authentication check
    Pagoda->>PluginAPI: Route to plugin endpoint
    PluginAPI->>PluginAPI: Plugin logic execution
    PluginAPI->>SDK_MODELS: Access Entity model
    SDK_MODELS->>DB: Execute database query
    DB-->>SDK_MODELS: Return data
    SDK_MODELS-->>PluginAPI: Entity instances
    PluginAPI-->>Pagoda: API response
    Pagoda-->>C: JSON response

    Note over C,DB: Complete plugin API request flow with model access
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

Through this 3-layer architecture design with Protocol-based model injection, Pagoda provides a completely independent plugin ecosystem, realizing a secure and extensible platform. Plugin developers can provide unique value while accessing Pagoda's core models through type-safe Protocol definitions, without creating implementation dependencies.