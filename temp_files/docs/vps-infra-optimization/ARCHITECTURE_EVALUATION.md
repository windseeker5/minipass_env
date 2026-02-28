# Architecture Evaluation: Container-per-Customer vs Alternatives

Generated: 2026-02-27

## Current Architecture Analysis

### Container-per-Customer Model (Current)

**Implementation**: Each customer gets a dedicated Docker container with:
- Individual Flask application instance
- Dedicated SQLite database
- Separate upload storage
- Isolated runtime environment

**Current Resource Usage** (4 customers):
- Average memory per customer: 221.5MB
- Total customer memory: 886MB
- Infrastructure overhead: ~400MB
- CPU usage: Minimal (<0.1% per customer)

## Architecture Alternatives Evaluation

### Option 1: Shared Multi-Tenant Application

#### Architecture Overview
```
Internet → nginx-proxy → Single Flask App Container
                            ├── Tenant ID routing
                            ├── Shared database with tenant_id
                            └── Shared file storage with tenant isolation
```

#### Implementation Details
- **Single Flask application** with tenant context switching
- **PostgreSQL database** with tenant_id column in all tables
- **Shared file storage** with customer subdirectories
- **Session-based tenant identification**
- **Middleware for tenant isolation**

#### Resource Projection
```
Current (4 customers):      886MB
Shared architecture:        ~200-300MB total
Savings:                    ~586-686MB (66-77% reduction)

At 50 customers:
Current projection:         11,075MB
Shared projection:          ~500-800MB
Savings:                    ~10,275-10,575MB (92-95% reduction)
```

#### Advantages
✅ **Massive resource savings** (70-90% RAM reduction)
✅ **Simplified deployment** (single container to manage)
✅ **Shared caching** benefits all customers
✅ **Centralized monitoring** and logging
✅ **Database optimization** (connection pooling, query optimization)
✅ **Code updates** deployed to all customers simultaneously
✅ **Cost efficiency** for hosting provider

#### Disadvantages
❌ **Complex tenant isolation** implementation required
❌ **Single point of failure** affects all customers
❌ **Security risks** if tenant isolation fails
❌ **Performance impact** if one customer overloads system
❌ **Database migration complexity**
❌ **Debugging complexity** with mixed tenant logs
❌ **Customization limitations** per customer

#### Implementation Complexity
**High** - Requires significant application refactoring
- Multi-tenant middleware development
- Database schema migration
- File storage reorganization
- Security audit requirements
- Extensive testing for tenant isolation

### Option 2: Microservices Architecture

#### Architecture Overview
```
Internet → API Gateway → Service Mesh
                         ├── Authentication Service
                         ├── Activity Management Service
                         ├── Payment Processing Service
                         ├── Notification Service
                         └── File Storage Service
```

#### Implementation Details
- **Service-based decomposition** by business function
- **Shared services** for common functionality
- **Customer-specific data isolation** within each service
- **API Gateway** for routing and load balancing
- **Event-driven communication** between services

#### Resource Projection (Conservative)
```
Services (estimated):
- API Gateway:              100MB
- Auth Service:             150MB
- Activity Service:         200MB
- Payment Service:          100MB
- Notification Service:     100MB
- File Storage Service:     150MB
- Database (PostgreSQL):    200MB
Total Base:                1,000MB

Per customer overhead:      ~10-20MB
At 50 customers:           1,500-2,000MB
```

#### Advantages
✅ **Horizontal scalability** - scale services independently
✅ **Technology diversity** - different languages/frameworks per service
✅ **Fault isolation** - service failures don't affect others
✅ **Team autonomy** - different teams can own different services
✅ **Deployment independence** - update services separately
✅ **Better resource utilization** - scale only what needs scaling

#### Disadvantages
❌ **Operational complexity** dramatically increased
❌ **Network latency** between services
❌ **Debugging difficulty** across service boundaries
❌ **Data consistency challenges**
❌ **Monitoring complexity** (distributed tracing required)
❌ **Development complexity** for small team
❌ **Infrastructure overhead** (service discovery, load balancers, etc.)

#### Implementation Complexity
**Very High** - Complete system redesign required
- Service boundary definition
- Data migration strategy
- Inter-service communication protocols
- Monitoring and observability setup
- DevOps pipeline restructuring

### Option 3: Hybrid Approach (Recommended)

#### Architecture Overview
```
Internet → nginx-proxy → Customer Routing Layer
                         ├── Shared Services Container
                         │   ├── Auth/Session Management
                         │   ├── Email Processing
                         │   ├── Payment Processing
                         │   └── Shared Database (PostgreSQL)
                         └── Customer-Specific Containers (Lightweight)
                             ├── Activity-specific logic only
                             ├── Customer-specific configurations
                             └── Upload storage (isolated)
```

#### Implementation Details
- **Shared infrastructure services** (auth, email, payments, database)
- **Lightweight customer containers** for activity-specific logic only
- **PostgreSQL database** with tenant isolation
- **Shared caching layer** for all customers
- **Gradual migration path** from current architecture

#### Resource Projection
```
Shared services:           ~400MB
Customer containers:       ~50-80MB each
Database (PostgreSQL):     ~200MB

At 4 customers:           ~800MB (10% saving)
At 50 customers:          ~3,000MB (72% saving vs current projection)
```

#### Advantages
✅ **Moderate resource savings** (50-70% at scale)
✅ **Maintains customer isolation** for sensitive operations
✅ **Gradual migration possible** from current architecture
✅ **Reduced operational complexity** vs full microservices
✅ **Shared infrastructure benefits** (caching, monitoring, auth)
✅ **Customer-specific customizations** still possible
✅ **Better fault isolation** than single shared app

#### Disadvantages
❌ **Still some container overhead** per customer
❌ **Mixed complexity** - benefits of neither pure approach
❌ **Database migration** still required
❌ **Service boundaries** need careful design

#### Implementation Complexity
**Medium** - Incremental refactoring possible
- Extract shared services first
- Migrate to PostgreSQL database
- Slim down customer containers
- Implement shared caching
- Gradual customer migration

### Option 4: Kubernetes-based Architecture

#### Architecture Overview
```
Kubernetes Cluster
├── Ingress Controller (nginx)
├── Shared Services Namespace
│   ├── Database (PostgreSQL)
│   ├── Redis Cache
│   ├── Authentication Service
│   └── File Storage Service
└── Customer Namespaces
    ├── Customer App Pods (auto-scaling)
    └── Customer-specific ConfigMaps/Secrets
```

#### Implementation Details
- **Kubernetes orchestration** with namespaces per customer
- **Auto-scaling** based on customer load
- **Shared persistent volumes** for database and cache
- **GitOps deployment** for customer configurations
- **Resource quotas** per customer namespace

#### Resource Utilization
- **Better resource efficiency** through Kubernetes scheduling
- **Auto-scaling** prevents resource waste
- **Resource quotas** prevent runaway usage
- **Shared node overhead** distributed across customers

#### Advantages
✅ **Production-grade orchestration**
✅ **Auto-scaling** capabilities
✅ **Better resource utilization**
✅ **Industry-standard deployment patterns**
✅ **Built-in monitoring** and logging
✅ **Rolling updates** and rollback capabilities

#### Disadvantages
❌ **Kubernetes learning curve** and operational overhead
❌ **Infrastructure complexity** significantly increased
❌ **Overkill for current scale** (4 customers)
❌ **Additional infrastructure costs**
❌ **Migration complexity** very high

## Recommendation Matrix

| Architecture | Resource Efficiency | Implementation Complexity | Operational Complexity | Risk Level | Timeline |
|--------------|-------------------|-------------------------|----------------------|------------|----------|
| **Current** | ⭐⭐ | ⭐ | ⭐⭐ | LOW | N/A |
| **Shared Multi-Tenant** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | HIGH | 4-6 weeks |
| **Microservices** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | HIGH | 8-12 weeks |
| **Hybrid** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | MEDIUM | 3-4 weeks |
| **Kubernetes** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | MEDIUM | 6-8 weeks |

## Strategic Recommendation

### Phase 1: Immediate Optimization (Current Architecture + Caching)
**Timeline**: 1-2 weeks
**Goal**: Address immediate performance issues while maintaining current architecture

1. Implement nginx-proxy caching
2. Optimize customer container configurations
3. Add comprehensive monitoring
4. Remove unnecessary containers (bloomcap)

**Expected Results**:
- 50-80% performance improvement
- Maintain stability and reliability
- Buy time for architectural planning

### Phase 2: Hybrid Architecture Migration (Recommended)
**Timeline**: 3-4 weeks
**Goal**: Optimize resource usage while maintaining customer isolation

**Migration Strategy**:
1. **Week 1**: Set up PostgreSQL database, migrate customer data
2. **Week 2**: Extract shared services (auth, email, payments)
3. **Week 3**: Implement shared caching layer
4. **Week 4**: Optimize customer containers, testing, deployment

**Benefits at 50 customers**:
- 72% memory reduction vs current projection
- Shared infrastructure benefits
- Maintained customer isolation
- Easier monitoring and maintenance

### Phase 3: Future Evaluation (6+ months)
**Consider**: Full multi-tenant or microservices architecture
**Triggers**:
- Growth beyond 30-40 customers
- Need for advanced features requiring service separation
- Team growth requiring microservice ownership models

## Implementation Roadmap

### Step 1: Database Migration
```sql
-- Migrate from SQLite to PostgreSQL with tenant isolation
CREATE DATABASE minipass_shared;
-- Add tenant_id columns to all tables
-- Implement row-level security
```

### Step 2: Shared Services Extraction
```yaml
# Shared services container
shared-services:
  image: minipass-shared-services
  services:
    - authentication
    - email-processing
    - payment-processing
    - session-management
```

### Step 3: Customer Container Optimization
```yaml
# Lightweight customer container
customer-app:
  image: minipass-customer-app
  environment:
    - TENANT_ID=${CUSTOMER_ID}
    - DATABASE_URL=postgresql://shared-db/minipass_shared
  volumes:
    - customer-uploads:/app/uploads
```

## Risk Mitigation Strategies

### For Hybrid Approach Migration
1. **Gradual Migration**: Migrate one customer at a time
2. **Rollback Plan**: Keep current containers during transition
3. **Data Backup**: Full backup before any database migration
4. **Testing**: Comprehensive testing in staging environment
5. **Monitoring**: Enhanced monitoring during migration period

### Success Metrics
- **Performance**: Response time improvement >50%
- **Resource Usage**: Memory reduction >40%
- **Reliability**: Zero customer-facing downtime during migration
- **Scalability**: Support for 25+ customers post-migration

## Conclusion

The **Hybrid Architecture** represents the optimal balance between resource efficiency, implementation complexity, and risk management for your current scale and growth trajectory.

Key reasons for this recommendation:
1. **Immediate resource savings** without complete system redesign
2. **Maintains customer isolation** for security and compliance
3. **Provides foundation** for future architectural evolution
4. **Manageable implementation** for a startup team
5. **Significant performance improvements** over current architecture

The current container-per-customer model served well during the prototype and early customer phase, but optimization is needed for sustainable growth. The hybrid approach provides the best path forward while preserving operational stability.