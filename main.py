import os
from db.init_db import init_database


def main():
    conn = init_database("app.db")
    print("Database initialized successfully.")
    print("Hello from the patch tool!")

    files = os.listdir(".")
    for file in files:
        print(file)


if __name__ == "__main__":
    main()
