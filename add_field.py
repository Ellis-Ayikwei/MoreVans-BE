import psycopg2

# Database connection parameters
DB_NAME = "morevans"
DB_USER = "postgres"
DB_PASSWORD = "@Toshib123"
DB_HOST = "localhost"
DB_PORT = "5432"

try:
    # Connect to the database
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

    cursor = conn.cursor()

    # Check if the column already exists
    cursor.execute(
        """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'common_item' AND column_name = 'model'
    """
    )

    if cursor.fetchone():
        print("Model column already exists in common_item table")
    else:
        # Add the model column
        cursor.execute(
            """
            ALTER TABLE common_item 
            ADD COLUMN model VARCHAR(100) DEFAULT ''
        """
        )
        conn.commit()
        print("Successfully added model column to common_item table")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
