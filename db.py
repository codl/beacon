import psycopg2
from os import getenv

def get_pg(application_name="beacon"):
    return psycopg2.connect(
        getenv("BEACON_POSTGRESQL", ""), application_name=application_name)


def setup_db():
    pg = get_pg(application_name="beacon migrations (db.py)")
    cur = pg.cursor()
    cur.execute('''
        SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'db_versions';
    ''')
    if cur.fetchone() is None:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS beacons (
                id serial PRIMARY KEY,
                collected_at timestamp without time zone DEFAULT now(),
                received_at timestamp without time zone DEFAULT now(),
                type text,
                body jsonb,
                count integer DEFAULT 1,
                CONSTRAINT beacons_type_collected_at_body_key UNIQUE (type, collected_at, body)
            );
            CREATE INDEX IF NOT EXISTS idx_beacons_collected_at ON beacons (collected_at);
            CREATE INDEX IF NOT EXISTS idx_beacons_type_collected_at ON beacons (type, collected_at);
            CREATE TABLE IF NOT EXISTS db_versions (
                version integer PRIMARY KEY
            );
            INSERT INTO db_versions VALUES (0);
            ''')
        version = 0
    else:
        cur.execute('''SELECT version FROM db_versions;''')
        row = cur.fetchone()
        if not row:
            raise Exception('Found DB but could not find DB version.')
        version = row[0]

    if version < 1:
        cur.execute('''
            CREATE TABLE auth_tokens (
                token text PRIMARY KEY
            );
            ALTER TABLE beacons
                ADD COLUMN authenticated
                    BOOLEAN
                    NOT NULL
                    DEFAULT 'f'
                ,
                DROP CONSTRAINT beacons_type_collected_at_body_key
                ,
                ADD CONSTRAINT const_uniqueness
                    UNIQUE (type, collected_at, authenticated, body)
            ;
            -- the unique constraint already creates a more detailed index
            DROP INDEX idx_beacons_type_collected_at;
        ''')
        version = 1

    if version < 2:
        cur.execute('''
            ALTER TABLE auth_tokens
                ADD COLUMN purpose
                    TEXT;
            ALTER TABLE beacons
                ADD COLUMN auth_purpose
                    TEXT;
        ''')


        version = 2

    if version < 4:
        cur.execute('''
            ALTER TABLE beacons
                ALTER COLUMN authenticated
                    DROP NOT NULL;
        ''')

        version = 4

    if version < 201903071309:
        cur.execute('''
            ALTER TABLE db_versions
                ALTER COLUMN version
                    TYPE bigint;
        ''')
        version = 201903071309

    if version < 201904140038:
        cur.execute('''
            CREATE FUNCTION date_quant(interval, timestamp with time zone)
                RETURNS timestamp with time zone
                LANGUAGE 'sql'
                IMMUTABLE STRICT
            AS $$

            WITH a AS(
                SELECT EXTRACT(EPOCH FROM $2)::BIGINT AS ts, EXTRACT(EPOCH FROM $1)::BIGINT AS precision
            )
            SELECT to_timestamp(ts - ts % precision) FROM a;

            $$;

            CREATE FUNCTION date_quant(interval, timestamp without time zone)
                RETURNS timestamp without time zone
                LANGUAGE 'sql'
                IMMUTABLE STRICT
            AS $$

                SELECT date_quant($1, $2 AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
                -- this is silly

            $$;
        ''')
        version = 201904140038

    if version < 201910210125:
        cur.execute('''
        ALTER TABLE beacons
            ALTER COLUMN collected_at
                TYPE timestamptz USING collected_at AT TIME ZONE 'UTC';

        ALTER TABLE beacons
            ALTER COLUMN received_at
                TYPE timestamptz USING received_at AT TIME ZONE 'UTC';
    ''')
        version = 201910210125

    if version < 202010280001:
        cur.execute('''
        ALTER TABLE beacons
            ADD COLUMN received_from
                inet;
    ''')
        version = 202010280001

    cur.execute(
        '''
        DELETE FROM db_versions;
        INSERT INTO db_versions VALUES (%s);
        ''', (version, ))

    pg.commit()


if __name__ == '__main__':
    setup_db()
