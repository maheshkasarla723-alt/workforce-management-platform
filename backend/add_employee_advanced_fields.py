from sqlalchemy import text

from backend.database import engine


def add_column(
    connection,
    column_name,
    column_definition
):
    """
    Add a column only if it does not already exist.
    """

    result = connection.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'employees'
              AND column_name = :column_name
            """
        ),
        {
            "column_name": column_name
        }
    )

    exists = result.first()

    if exists:

        print(
            f"{column_name} column already exists."
        )

        return

    connection.execute(
        text(
            f"""
            ALTER TABLE employees
            ADD COLUMN {column_name}
            {column_definition}
            """
        )
    )

    print(
        f"{column_name} column added successfully."
    )


def main():

    print(
        "Starting Employee advanced fields migration..."
    )

    with engine.begin() as connection:

        # ------------------------------------------------
        # STATUS
        # ------------------------------------------------

        add_column(
            connection,
            "status",
            (
                "VARCHAR(30) "
                "NOT NULL "
                "DEFAULT 'Active'"
            )
        )

        # ------------------------------------------------
        # JOINING DATE
        # ------------------------------------------------

        add_column(
            connection,
            "joining_date",
            "DATE"
        )

        # ------------------------------------------------
        # SKILLS
        # ------------------------------------------------

        add_column(
            connection,
            "skills",
            "TEXT"
        )

        # ------------------------------------------------
        # PROFILE METADATA
        # PostgreSQL JSONB
        # ------------------------------------------------

        add_column(
            connection,
            "profile_metadata",
            "JSONB"
        )

    print(
        "Employee advanced fields migration completed."
    )


if __name__ == "__main__":

    main()