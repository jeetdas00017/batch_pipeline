import random
from datetime import datetime

from faker import Faker
from psycopg2.extras import execute_values

from extract.utils.config import SOURCE_SCHEMA
from extract.utils.db_utils import get_pg_connection
from extract.utils.logging_config import logger

fake = Faker()

# ----------------------------
# PostgreSQL Connection
# ----------------------------

def get_connection():
    return get_pg_connection()


# ----------------------------
# Helper Functions
# ----------------------------
def _qualified_table_name(table_name: str) -> str:
    if SOURCE_SCHEMA:
        return f"{SOURCE_SCHEMA}.{table_name}"
    return table_name


def get_next_id(cursor, table_name, id_column):
    cursor.execute(f"""
        SELECT COALESCE(MAX({id_column}),0)+1
        FROM {_qualified_table_name(table_name)}
    """)
    return cursor.fetchone()[0]


def row_count(cursor, table_name):
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM {_qualified_table_name(table_name)}
    """)
    return cursor.fetchone()[0]


# ----------------------------
# Customer Generator
# ----------------------------
def generate_customers(cursor, count=10):

    start_id = get_next_id(cursor, "customers", "customer_id")

    rows = []

    for i in range(count):
        rows.append((
            start_id + i,
            fake.first_name(),
            fake.last_name(),
            fake.email(),
            fake.msisdn()[:10],
            fake.city(),
            "India",
            datetime.now(),
            datetime.now()
        ))

    execute_values(
        cursor,
        f"""
        INSERT INTO {_qualified_table_name('customers')}
        (
            customer_id,
            first_name,
            last_name,
            email,
            phone,
            city,
            country,
            created_at,
            updated_at
        )
        VALUES %s
        """,
        rows
    )

    return count


# ----------------------------
# Product Generator
# ----------------------------
def generate_products(cursor, count=10):

    brands = {
        "Apple": ["iPhone", "MacBook", "iPad", "AirPods"],
        "Samsung": ["Galaxy", "Watch", "TV"],
        "Sony": ["Bravia", "WH-1000XM5"],
        "Dell": ["Inspiron", "XPS"],
        "Lenovo": ["ThinkPad", "IdeaPad"]
    }

    categories = {
        "iPhone": ("Electronics", "Smartphones"),
        "Galaxy": ("Electronics", "Smartphones"),
        "MacBook": ("Electronics", "Laptops"),
        "Inspiron": ("Electronics", "Laptops"),
        "XPS": ("Electronics", "Laptops"),
        "ThinkPad": ("Electronics", "Laptops"),
        "IdeaPad": ("Electronics", "Laptops"),
        "iPad": ("Electronics", "Tablet"),
        "Watch": ("Electronics", "Smartwatch"),
        "TV": ("Electronics", "Television"),
        "Bravia": ("Electronics", "Television"),
        "WH-1000XM5": ("Electronics", "Headphones"),
        "AirPods": ("Electronics", "Earbuds")
    }

    start_id = get_next_id(cursor, "products", "product_id")

    rows = []

    for i in range(count):

        brand = random.choice(list(brands.keys()))
        product = random.choice(brands[brand])

        category, sub_category = categories[product]

        cost = random.randint(1000, 80000)
        price = round(cost * random.uniform(1.15, 1.45), 2)

        rows.append((
            start_id + i,
            f"{product} {random.randint(1,20)}",
            category,
            sub_category,
            brand,
            price,
            cost,
            datetime.now(),
            datetime.now()
        ))

    execute_values(
        cursor,
        f"""
        INSERT INTO {_qualified_table_name('products')}
        (
            product_id,
            product_name,
            category,
            sub_category,
            brand,
            price,
            cost,
            created_at,
            updated_at
        )
        VALUES %s
        """,
        rows
    )

    return count


# ----------------------------
# Order Generator
# ----------------------------
def generate_orders(cursor, count=20):

    cursor.execute(f"""
        SELECT customer_id
        FROM {_qualified_table_name('customers')}
    """)
    customers = [x[0] for x in cursor.fetchall()]

    cursor.execute(f"""
        SELECT product_id, price
        FROM {_qualified_table_name('products')}
    """)
    products = cursor.fetchall()

    start_id = get_next_id(cursor, "orders", "order_id")

    payment_methods = [
        "UPI",
        "CARD",
        "NETBANKING",
        "CASH"
    ]

    statuses = [
        "PROCESSING",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED"
    ]

    rows = []

    for i in range(count):

        customer = random.choice(customers)
        product_id, price = random.choice(products)

        quantity = random.randint(1, 5)
        discount = random.choice([0, 2, 5, 10])
        price = float(price)

        total = round(quantity * price * (1 - discount / 100),2)

        rows.append((
            start_id + i,
            customer,
            product_id,
            datetime.now(),
            quantity,
            price,
            discount,
            total,
            random.choice(statuses),
            random.choice(payment_methods),
            datetime.now(),
            datetime.now()
        ))

    execute_values(
        cursor,
        f"""
        INSERT INTO {_qualified_table_name('orders')}
        (
            order_id,
            customer_id,
            product_id,
            order_date,
            quantity,
            unit_price,
            discount,
            total_amount,
            order_status,
            payment_method,
            created_at,
            updated_at
        )
        VALUES %s
        """,
        rows
    )

    return count


# ----------------------------
# Main Function
# ----------------------------
def generate_fake_data(
    customer_count=10,
    product_count=10,
    order_count=20
):

    conn = get_connection()
    cur = conn.cursor()

    logger.info("Starting fake data insert for schema=%s", SOURCE_SCHEMA)

    before = {
        "customers": row_count(cur, "customers"),
        "products": row_count(cur, "products"),
        "orders": row_count(cur, "orders")
    }

    generate_customers(cur, customer_count)
    generate_products(cur, product_count)
    generate_orders(cur, order_count)

    conn.commit()

    after = {
        "customers": row_count(cur, "customers"),
        "products": row_count(cur, "products"),
        "orders": row_count(cur, "orders")
    }

    print("\nInsertion Summary")
    print("-" * 50)

    for table in before:
        added = after[table] - before[table]
        print(
            f"{table:<12} Before={before[table]:<5} "
            f"After={after[table]:<5} Added={added}"
        )

    logger.info("Completed fake data insert for schema=%s", SOURCE_SCHEMA)

    cur.close()
    conn.close()


if __name__ == "__main__":
    generate_fake_data(
        customer_count=20,
        product_count=10,
        order_count=50
    )