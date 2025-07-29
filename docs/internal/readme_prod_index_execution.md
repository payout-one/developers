@ -0,0 +1,169 @@
# Production Index Creation Guide

This guide provides 5 SQL files for manually creating database indexes in production. **Execute these one by one** to control database load and avoid overwhelming the production system.

## 📋 **Execution Order & Files**

1. **`01_account_customers_indexes.sql`** - 11 B-tree indexes for account_customers
2. **`02_finance_checkouts_indexes.sql`** - 13 B-tree indexes for finance_checkouts
3. **`03_finance_transactions_indexes.sql`** - 21 B-tree indexes for finance_transactions
4. **`04_reference_lookup_indexes.sql`** - 15 B-tree indexes for lookup tables
5. **`05_search_gin_indexes.sql`** - 11 GIN indexes for fuzzy text search

## 🚨 **Critical Safety Guidelines**

### **Before You Start:**
- ✅ **Backup your database** before creating any indexes
- ✅ **Schedule during low-traffic periods** (maintenance windows)
- ✅ **Monitor database performance** during execution
- ✅ **Have a rollback plan** ready

### **Execution Method:**
```bash
# Connect to your production database
psql "your-production-database-connection-string"

# Execute ONE index at a time, monitoring each:
\i 01_account_customers_indexes.sql

# Wait and monitor before continuing...
# Check: SELECT * FROM pg_stat_activity WHERE query LIKE '%CREATE INDEX%';
```

## ⚡ **Performance Impact Expectations**

| File | Estimated Duration | Expected Impact |
|------|-------------------|-----------------|
| `01_account_customers_indexes.sql` | 5-15 minutes | **Low** - Small table |
| `02_finance_checkouts_indexes.sql` | 15-45 minutes | **Medium** - Moderate table size |
| `03_finance_transactions_indexes.sql` | **30-90 minutes** | **HIGH** - Large table |
| `04_reference_lookup_indexes.sql` | 10-30 minutes | **Low-Medium** - Mixed sizes |
| `05_search_gin_indexes.sql` | 20-60 minutes | **Medium-High** - GIN indexes are slower |

## 🔍 **Monitoring Commands**

### **Check Index Creation Progress:**
```sql
-- See active index creation processes
SELECT pid, query, state, query_start
FROM pg_stat_activity
WHERE query LIKE '%CREATE INDEX%';

-- Monitor index build progress (PostgreSQL 12+)
SELECT
    schemaname, tablename, attname,
    n_distinct, correlation
FROM pg_stats
WHERE tablename IN ('account_customers', 'finance_checkouts', 'finance_transactions');
```

### **Check Database Load:**
```sql
-- Monitor database connections and load
SELECT count(*) as active_connections, state
FROM pg_stat_activity
GROUP BY state;

-- Check for blocking queries
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

## 🛠️ **Recommended Execution Strategy**

### **Phase 1: Low-Risk Indexes (Day 1)**
```bash
# Execute during low-traffic period
psql "connection-string" -f 01_account_customers_indexes.sql
psql "connection-string" -f 04_reference_lookup_indexes.sql
```

### **Phase 2: Medium-Risk Indexes (Day 2-3)**
```bash
# Execute finance_checkouts indexes one by one
psql "connection-string" -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_checkouts_account_type_date ON finance_checkouts (account_id, type, inserted_at);"
# Wait 10-15 minutes, monitor load...
psql "connection-string" -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_checkouts_account_currency_date ON finance_checkouts (account_id, currency, inserted_at);"
# Continue one by one...
```

### **Phase 3: High-Risk Indexes (Weekend)**
```bash
# Execute finance_transactions indexes during maintenance window
# These are the largest and most critical - monitor closely
psql "connection-string" -f 03_finance_transactions_indexes.sql
```

### **Phase 4: GIN Indexes (Planned Maintenance)**
```bash
# GIN indexes take longer and use more resources
psql "connection-string" -f 05_search_gin_indexes.sql
```

## 🚫 **Emergency Rollback**

If you need to cancel index creation:
```sql
-- Find the process ID
SELECT pid, query FROM pg_stat_activity WHERE query LIKE '%CREATE INDEX%';

-- Terminate the process (this will rollback the index creation)
SELECT pg_terminate_backend(pid_number_here);

-- Drop partially created indexes if needed
DROP INDEX CONCURRENTLY IF EXISTS index_name_here;
```

## ✅ **Verification After Completion**

```sql
-- Verify all indexes were created successfully
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Check index sizes
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE indexrelname LIKE 'idx_%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## 📊 **Expected Performance Improvements**

After completing all indexes:
- **Account customers queries**: 50-80% faster
- **Checkout listing**: 642ms → ~10ms (95% improvement)
- **Reference search**: 1,294ms → ~50ms (96% improvement)
- **Transaction filtering**: 60-90% faster
- **Fuzzy text search**: 90%+ faster with GIN indexes

## 🆘 **Support Contacts**

- **Database Team**: [your-db-team@company.com]
- **Emergency Escalation**: [emergency-contact]
- **Monitoring Dashboard**: [your-monitoring-url]

---

**⚠️ Remember**: Better to take 2-3 days executing safely than to overwhelm production with all indexes at once!
