# warehouse_app

SQLite inventory database for a sports warehouse using only one table: `inventory`.

## Create the database

Run from the project root:

```bash
python3 scripts/init_db.py
```

This creates or recreates `warehouse_inventory.db`.

## Files

- `sql/schema.sql` defines the single `inventory` table.
- `sql/seed.sql` inserts sample warehouse inventory rows.
- `scripts/init_db.py` initializes the database.

## Example query

```sql
SELECT
	sku,
	product_name,
	quantity_on_hand,
	quantity_reserved,
	(quantity_on_hand - quantity_reserved) AS quantity_available,
	reorder_level
FROM inventory
ORDER BY product_name;
```