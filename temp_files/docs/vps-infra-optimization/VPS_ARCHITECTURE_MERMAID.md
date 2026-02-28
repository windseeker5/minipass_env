# Minipass VPS Architecture - Mermaid Diagrams

## Complete System Architecture

```mermaid
graph TB
    Internet[🌐 Internet] --> nginxproxy[nginx-proxy<br/>Port 80/443<br/>60.8MB RAM]

    nginxproxy --> |minipass.me| flaskproxy[flask-controller-proxy<br/>6.4MB RAM]
    nginxproxy --> |lhgi.minipass.me| lhgi[minipass_lhgi<br/>248MB RAM<br/>21.9MB uploads]
    nginxproxy --> |kdc.minipass.me| kdc[minipass_kdc<br/>217MB RAM<br/>1.1MB uploads]
    nginxproxy --> |heq.minipass.me| heq[minipass_heq<br/>263MB RAM<br/>0.7MB uploads]
    nginxproxy --> |testdel...| testdel[minipass_testdel<br/>157MB RAM<br/>0.3MB uploads]
    nginxproxy --> |mail.minipass.me| mailcert[mail-cert-request<br/>8MB RAM]
    nginxproxy --> |bloomcap.ca| bloomcap[bloomcap<br/>7.8MB RAM<br/>⚠️ Remove]

    flaskproxy --> |proxy_pass :5000| hostapp[Host Flask App<br/>176MB RAM<br/>Main Application]

    mailcert --> mailserver[mailserver<br/>311MB RAM<br/>Ports: 25,587,993]

    letsencrypt[nginx-letsencrypt<br/>30MB RAM<br/>SSL Automation] --> nginxproxy

    hostapp --> hostdb[(SQLite<br/>Main DB)]
    lhgi --> lhgidb[(SQLite<br/>LHGI DB)]
    kdc --> kdcdb[(SQLite<br/>KDC DB)]
    heq --> heqdb[(SQLite<br/>HEQ DB)]
    testdel --> testdeldb[(SQLite<br/>TestDel DB)]

    classDef customerContainer fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef infrastructure fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef database fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef problem fill:#ffebee,stroke:#c62828,stroke-width:3px

    class lhgi,kdc,heq,testdel customerContainer
    class nginxproxy,flaskproxy,letsencrypt,mailserver,mailcert infrastructure
    class hostdb,lhgidb,kdcdb,heqdb,testdeldb database
    class bloomcap problem
```

## Network Flow Architecture

```mermaid
flowchart TD
    A[🌐 User Request] --> B{nginx-proxy<br/>SSL Termination}

    B --> |minipass.me| C[flask-controller-proxy]
    B --> |customer.minipass.me| D[Customer Container]
    B --> |mail.minipass.me| E[Mail Services]

    C --> |/static/*| F[Direct File Serve<br/>⚡ 10-100x faster]
    C --> |/* proxy_pass| G[Host Flask App<br/>:5000]

    D --> H[Customer Flask App<br/>:8889]

    G --> I[(Main SQLite DB)]
    H --> J[(Customer SQLite DB)]

    E --> K[mailserver<br/>Full Email Stack]

    classDef fast fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef slow fill:#ffcdd2,stroke:#c62828,stroke-width:2px

    class F fast
    class D,H slow
```

## Resource Usage Breakdown

```mermaid
pie title VPS Memory Usage (7.6GB Total)
    "Available Memory" : 5151
    "Customer Containers" : 886
    "Mail Server" : 311
    "nginx-proxy" : 61
    "Other Infrastructure" : 151
```

## Performance Bottleneck Analysis

```mermaid
graph LR
    A[User Request] --> B[nginx-proxy<br/>❌ No Cache]
    B --> C[Customer Container<br/>❌ Every Request]
    C --> D[Flask App<br/>❌ Full Processing]
    D --> E[SQLite Query<br/>❌ No Connection Pool]
    E --> F[File System<br/>❌ No Optimization]

    G[🔥 PROBLEM: No caching at ANY level] --> B
    H[🔥 PROBLEM: 21.9MB LHGI uploads] --> F
    I[🔥 PROBLEM: No compression] --> C

    classDef problem fill:#ffebee,stroke:#c62828,stroke-width:3px
    class B,C,D,E,F problem
```

## Scaling Projection

```mermaid
graph LR
    A[4 Customers<br/>33.5% Memory] --> B[10 Customers<br/>55% Memory]
    B --> C[15 Customers<br/>76% Memory<br/>⚠️ Plan Migration]
    C --> D[20 Customers<br/>97% Memory<br/>❌ Critical]
    D --> E[25+ Customers<br/>>100% Memory<br/>❌ Impossible]

    classDef safe fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef warning fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef critical fill:#ffebee,stroke:#c62828,stroke-width:2px

    class A,B safe
    class C warning
    class D,E critical
```

## Container-per-Customer Current Model

```mermaid
graph TB
    subgraph "Customer Isolation Model"
        subgraph "LHGI Customer"
            L1[Flask App<br/>248MB RAM]
            L2[(SQLite DB)]
            L3[/Uploads: 21.9MB/]
        end

        subgraph "KDC Customer"
            K1[Flask App<br/>217MB RAM]
            K2[(SQLite DB)]
            K3[/Uploads: 1.1MB/]
        end

        subgraph "HEQ Customer"
            H1[Flask App<br/>263MB RAM]
            H2[(SQLite DB)]
            H3[/Uploads: 0.7MB/]
        end

        subgraph "TestDel Customer"
            T1[Flask App<br/>157MB RAM]
            T2[(SQLite DB)]
            T3[/Uploads: 0.3MB/]
        end
    end

    Internet --> Router[nginx-proxy<br/>Routes by subdomain]
    Router --> L1
    Router --> K1
    Router --> H1
    Router --> T1

    classDef customer fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    class L1,K1,H1,T1 customer
```

## Recommended Optimization Flow

```mermaid
graph TD
    A[Current: No Caching] --> B[Phase 1: Add nginx Cache<br/>🚀 50-80% improvement]
    B --> C[Phase 2: Optimize Images<br/>🚀 Reduce LHGI uploads]
    C --> D[Phase 3: Remove Unused<br/>🚀 Remove bloomcap]
    D --> E[Phase 4: Monitor<br/>📊 Track performance]

    F[Future: Hybrid Architecture] --> G[Shared Services<br/>Auth, Email, Payments]
    G --> H[Lightweight Customers<br/>~50MB each vs 221MB]
    H --> I[PostgreSQL Database<br/>Connection pooling]

    E -.-> |When approaching<br/>15-20 customers| F

    classDef immediate fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef future fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class A,B,C,D,E immediate
    class F,G,H,I future
```

## Email Infrastructure Detail

```mermaid
graph TB
    Internet --> |Port 25,587| SMTP[SMTP Receiver]
    Internet --> |Port 993| IMAP[IMAP Server]

    SMTP --> Mail[mailserver Container<br/>311MB RAM]
    IMAP --> Mail

    Mail --> Process[Email Processing<br/>Payment Detection<br/>Customer Notifications]
    Process --> Integration[Integration with<br/>Flask Applications]

    Mail --> Storage[Email Storage<br/>./maildata volume]
    Mail --> Config[Mail Configuration<br/>./config volume]
    Mail --> SSL[SSL Certificates<br/>mail.minipass.me]

    classDef mail fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    class Mail,Process,Integration mail
```

## Port Mapping Overview

```mermaid
graph LR
    subgraph "External Ports"
        P80[Port 80<br/>HTTP]
        P443[Port 443<br/>HTTPS]
        P25[Port 25<br/>SMTP]
        P587[Port 587<br/>SMTP Submit]
        P993[Port 993<br/>IMAPS]
    end

    subgraph "Internal Services"
        P80 --> nginx
        P443 --> nginx[nginx-proxy]
        P25 --> mail[mailserver]
        P587 --> mail
        P993 --> mail

        nginx --> |proxy| host[Host:5000<br/>Main App]
        nginx --> |proxy| cust[Customers:8889]
    end

    classDef external fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef internal fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px

    class P80,P443,P25,P587,P993 external
    class nginx,mail,host,cust internal
```