# Database Dump for Remote Server

## Quick Create Password-Protected Dump

```bash
# Interactive (will prompt for password)
./scripts/create_dump_for_remote.sh

# With password as argument
./scripts/create_dump_for_remote.sh "your_secure_password"
```

## Manual Method

If you already have a dump file:

```bash
# Create password-protected ZIP from existing dump
cd dumps
zip -P "your_secure_password" -9 mcraes_full_dump_20251204_192859.zip mcraes_full_dump_20251204_192859.dump

# Remove original dump to save space
rm mcraes_full_dump_20251204_192859.dump
```

## Extract and Restore

```bash
# Extract the ZIP file
unzip -P "your_secure_password" dumps/mcraes_full_dump_20251204_192859.zip

# Restore to production
./scripts/restore_database_dump.sh dumps/mcraes_full_dump_20251204_192859.dump production_db postgres prod-host.com 5432
```

## Current Dump File

The latest dump file is: `dumps/mcraes_full_dump_20251204_192859.dump` (42MB)

To create a password-protected version:
```bash
cd dumps
zip -P "your_password" -9 mcraes_full_dump_20251204_192859.zip mcraes_full_dump_20251204_192859.dump
```

