from sqlalchemy import text

from backend.database import engine


def add_manager_column():

    sql = """
    ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS manager_id
    INTEGER
    REFERENCES employees(id);
    """

    with engine.begin() as connection:
        connection.execute(text(sql))

    print("manager_id column added successfully.")


if __name__ == "__main__":
    add_manager_column()