# Column Rename Migration Summary

This document summarizes all the changes made to rename database columns and update related code in the LangExtract project.

## Database Changes

### Column Renames

- `text_embedding` → `embedding`
- `original_text` → `content`

### Migration Files

1. **`db/migrations/002_rename_columns.sql`** - New migration file for column renames
2. **`db/migrations/001_create_embeddings_table.sql`** - Updated to use new column names

### Database Functions Updated

- `match_embeddings()` function updated to use new column names
- Column comments updated to reflect new names

#### Function Update Commands

**Delete the old function:**

```sql
DROP FUNCTION IF EXISTS match_embeddings(vector(1536), float, integer);
```

**Create the new function with updated column names:**

```sql
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    chunk_id VARCHAR(255),
    document_id VARCHAR(255),
    content TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.chunk_id,
        e.document_id,
        e.content,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

## Code Changes

### Core Files Updated

1. **`core/vector_storage.py`**

   - Updated `_prepare_embedding_record()` method to use new column names
   - Changed `text_embedding` → `embedding`
   - Changed `original_text` → `content`

2. **`core/processor.py`**
   - Variable names remain the same (internal logic unchanged)
   - Only database column references were updated

### API Files Updated

1. **`api/serializers.py`**
   - Updated `ProcessedDocumentSerializer` to use `content` instead of `original_text`

### Custom Components Updated

1. **`custom_component/langextract_component.py`**

   - Updated `ProcessingResult` class to use `content` instead of `original_text`
   - Updated constructor calls

2. **`custom_component/langextract_langflow_component.py`**

   - Updated `ProcessingResult` class to use `content` instead of `original_text`
   - Updated all constructor calls and data mappings

3. **`custom_component/langextract_langflow_simple.py`**
   - Updated data mapping to use `content` instead of `original_text`

### Documentation Files Updated

1. **`VECTOR_STORAGE_README.md`**

   - Updated table schema examples
   - Updated column references in examples
   - Updated indexing documentation

2. **`README.md`**

   - Updated example JSON structure

3. **`custom_component/README.md`**

   - Updated field documentation

4. **`plan.md`**
   - Updated example data structure

## Migration Scripts

### Apply Migration

- **`apply_column_rename.py`** - Script to apply the column rename migration
- Connects to database using environment variables
- Safely renames columns and updates functions
- Includes verification steps

### Rollback Migration

- **`rollback_column_rename.py`** - Script to revert changes if needed
- Confirms rollback with user input
- Restores original column names and functions

## Environment Variables Required

The migration scripts require these environment variables:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=langextract
DB_USER=postgres
DB_PASSWORD=your_password
```

## How to Apply the Migration

1. **Set environment variables** for your database connection
2. **Run the migration script**:
   ```bash
   cd langextract
   python apply_column_rename.py
   ```
3. **Verify the changes** by checking the database structure

## How to Rollback (if needed)

1. **Run the rollback script**:
   ```bash
   cd langextract
   python rollback_column_rename.py
   ```
2. **Confirm the rollback** when prompted

## Impact Analysis

### Breaking Changes

- **Database queries** using old column names will fail
- **API responses** will now return `content` instead of `original_text`
- **Custom components** expecting `original_text` will need updates

### Compatibility

- **New installations** will work with the new column names
- **Existing installations** must run the migration script
- **Code changes** are backward-incompatible

## Testing Recommendations

1. **Test database queries** after migration
2. **Verify API endpoints** return correct field names
3. **Test custom components** with new field names
4. **Check vector similarity search** functionality
5. **Validate data integrity** after migration

## Notes

- The migration is **irreversible** without the rollback script
- **Backup your database** before running the migration
- **Test in development** environment first
- **Update any external integrations** that may reference old column names
