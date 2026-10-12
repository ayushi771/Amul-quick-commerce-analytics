from pipeline.db import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT current_database(), current_user, current_schema()"
        )
        print("DATABASE:", cur.fetchone())

        cur.execute(
            "SELECT table_schema, table_name "
            "FROM information_schema.tables "
            "WHERE table_name = 'dim_product'"
        )
        print("DIM_PRODUCT:", cur.fetchall())