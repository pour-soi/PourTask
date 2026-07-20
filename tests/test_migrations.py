def test_migration_is_idempotent(database):
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 1
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 1
