"""Classifies transactions as money-in vs money-out.

IMPORTANT: `transactions.amount` is NOT reliably signed in this schema. Deposits,
purchases, and usage bills are all stored as positive values - the `transaction_type`
string (e.g. 'ELECTRICITY_USAGE' vs 'WALLET_TOPUP') is what actually tells you the
direction, not the sign of `amount`. The one exception is ADJUSTMENT_* (from
/adjust-account/), which genuinely is signed: positive for a credit, negative for a debit.

Any report that filters on `tx.amount > 0` / `tx.amount < 0` to separate collections from
billing will silently misclassify almost every row. Use these fragments instead.

These are raw SQL fragments meant to be concatenated into a larger query string before it
reaches cursor.execute() - the query as a whole is still fully parameterized elsewhere via
%s placeholders, so this does not introduce any injection risk. `%` characters are doubled
(%%) because psycopg2 treats a single `%` in the final query text as the start of a
placeholder.
"""

MONEY_IN_SQL = """(
    tx.transaction_type IN ('WALLET_TOPUP', 'RENT_PAYMENT', 'UTILITY_PAYMENT', 'CREDIT_NOTE')
    OR tx.transaction_type LIKE '%%_PURCHASE'
    OR (tx.transaction_type LIKE 'ADJUSTMENT_%%' AND tx.amount > 0)
)"""

MONEY_OUT_SQL = """(
    tx.transaction_type LIKE '%%_BILL'
    OR tx.transaction_type LIKE '%%_USAGE'
    OR (tx.transaction_type LIKE 'ADJUSTMENT_%%' AND tx.amount < 0)
)"""