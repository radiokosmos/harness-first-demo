`bin/reconcile <model>` compares a daily model with its source, but the source side of two checks is still a TODO in bin/lib/reconcile.py: completeness() and keys().
Implement them. Done when `bin/reconcile fct_activity_daily` runs and reports real numbers, and `bin/test-reconcile` passes. Keep the change inside bin/lib/reconcile.py.
