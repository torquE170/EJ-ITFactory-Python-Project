from book import Book
from sql_conn import SqlDB
from user_settings import UserSettings
from mysql.connector import IntegrityError, ProgrammingError


class Library:

    def __init__(self, entries = None):
        if entries is None:
            entries = list()
        self.entries = entries

    def __repr__(self):
        if len(self.entries):
            typed_out = "-" * 60 + "\n"
        else:
            typed_out = ""
        for entry in self.entries:
            typed_out += f"{entry}\n"
            typed_out += "-" * 60 + "\n"
        return typed_out

    def add_entry(self, new_book):
        quantity = int(input("quantity: "))
        new_entry = LibraryEntry(new_book, quantity)
        self.entries.append(new_entry)

class LibraryEntry:

    def __init__(self, book: Book, quantity, available = None):
        self.book = book
        self.quantity = quantity
        if available is None:
            self.available = quantity
        else:
            self.available = available

    def __repr__(self):
        typed_out = f"{self.book}\n"
        typed_out += f"Quantity = {self.quantity}, Available = {self.available}"
        return typed_out

    @staticmethod
    def get_entry():
        new_book = Book.get_book()
        quantity = int(input("Quantity: "))
        new_entry = LibraryEntry(new_book, quantity)
        return new_entry

class BookStore:

    db_table = "BookStore"
    def __init__(self, entries = None):
        if entries is None:
            entries = list()
        self.entries = entries

    def __repr__(self):
        if len(self.entries):
            typed_out = f" {self.db_table} ".center(60, "-")
            typed_out += "\n"
        else:
            typed_out = ""
        for entry in self.entries:
            typed_out += f"{entry}\n"
            typed_out += "-" * 60 + "\n"
        return typed_out


    def save_entry(self, new_entry):
        next_id = SqlDB.get_last_id(BookStore.db_table, UserSettings.use_sqlite3) + 1
        # self.entries.append(BookStoreEntry(new_entry, next_id))
        this_entry = BookStoreEntry(new_entry, next_id)
        try:
            saved_entry = this_entry.save_to_db()
            self.entries.append(saved_entry)
        except IntegrityError:
            print(f"Book not added! \"{this_entry.entry.book.name}\" is already in store")
            print()

    @staticmethod
    def add_entry():
        """Use for entering a book from keyboard and saving it to database"""
        if UserSettings.at_cli:
            UserSettings.clear()
        print(f" Add book ".center(60, "-"))
        new_entry = BookStoreEntry.get_entry()
        try:
            new_entry.db_id = SqlDB.get_last_id(BookStore.db_table, UserSettings.use_sqlite3) + 1
            new_entry.save_to_db()
        except ProgrammingError:
            print(f"Table {BookStore.db_table} not available")
            print()
            try:
                BookStore.init_db(BookStore.db_table)
                print(f"Created new table {BookStore.db_table}")
                print()
                new_entry.db_id = SqlDB.get_last_id(BookStore.db_table, UserSettings.use_sqlite3) + 1
                new_entry.save_to_db()
            except ProgrammingError:
                print(f"Tried to make new {BookStore.db_table}, and failed")
                print("Exiting")
                print()
                return
            except IntegrityError:
                print(f"Book not added! \"{new_entry.entry.book.name}\" is already in store")
                print()
            return
        except IntegrityError:
            print(f"Book not added! \"{new_entry.entry.book.name}\" is already in store")
            print()

    @staticmethod
    def list_entries(table = db_table):
        if UserSettings.at_cli:
            UserSettings.clear()
        book_store = BookStore()
        list_query = f"""
        SELECT ID, Name, Author, Quantity, Available FROM {table};
        """
        try:
            books_list = SqlDB.sql_query_result(list_query, use_sqlite3=UserSettings.use_sqlite3)
        except ProgrammingError:
            print(f"Table {table} not available")
            print()
            return
        for entry in books_list:
            book_store.entries.append(BookStoreEntry(LibraryEntry(Book(entry[1], entry[2]), entry[3], entry[4]), entry[0]))
        print(book_store)  # or return it

    @staticmethod
    def search_book(table = db_table):
        if UserSettings.at_cli:
            UserSettings.clear()

        search_by = ""
        opt = -1
        while opt != 0:
            print("Search books by:")
            print("1 - Name")
            print("2 - Author")
            print()
            print("0 - Cancel")
            opt = UserSettings.read_menu_option(">> ")
            print()
            if opt == 1:
                search_by = "Name"
                break
            if opt == 2:
                search_by = "Author"
                break
            if opt == 0:
                print("Search canceled")
                return
        if UserSettings.at_cli:
            UserSettings.clear()
        keyword = input(f"Search books by {search_by}: ")

        queried_books = BookStore()
        search_query = f"""
        SELECT ID, Name, Author, Quantity, Available FROM {table} WHERE {search_by} LIKE "%{keyword}%";
        """
        try:
            result_list = SqlDB.sql_query_result(search_query, use_sqlite3=UserSettings.use_sqlite3)
        except ProgrammingError:
            print(f"Table {table} not available")
            print()
            return
        for entry in result_list:
            queried_books.entries.append(BookStoreEntry(LibraryEntry(Book(entry[1], entry[2]), entry[3], entry[4]), entry[0]))
        if len(queried_books.entries):
            print(queried_books)  # or return it
        else:
            print("No results\n")

    @staticmethod
    def delete_book(table = db_table):
        if UserSettings.at_cli:
            UserSettings.clear()

        delete_by = ""
        opt = -1
        while opt != 0:
            print("Delete book by:")
            print("1 - ID")
            print("2 - Name")
            print()
            print("0 - Cancel")
            opt = UserSettings.read_menu_option(">> ")
            print()
            if opt == 1:
                delete_by = "ID"
                break
            if opt == 2:
                delete_by = "Name"
                break
            if opt == 0:
                print("Delete operation canceled")
                return
        if UserSettings.at_cli:
            UserSettings.clear()

        value = ""
        if delete_by == "ID":
            value = int(input("ID: "))
        if delete_by == "Name":
            value = input("Name: ")
            value = f"\"{value}\""

        delete_statement = f"""
        DELETE FROM {table} WHERE {delete_by}={value};
        """
        SqlDB.sql_query(delete_statement, table, use_sqlite3=UserSettings.use_sqlite3)
        print()
        select_query = f"""
        SELECT ID, Name FROM {table}
        WHERE {delete_by} = {value};
        """
        result = SqlDB.sql_query_result(select_query, use_sqlite3=UserSettings.use_sqlite3)
        if len(result) == 0:
            print(f"Book with {delete_by}: {value} has been deleted")
            print()


    @staticmethod
    def init_db(db_table, drop = False):
        query_init = f'''
            CREATE TABLE {db_table} (
            ID INT NOT NULL,
            Name VARCHAR(50) NOT NULL UNIQUE,
            Author VARCHAR(128) NOT NULL,
            Quantity INT NOT NULL,
            Available INT NOT NULL,
            Publisher VARCHAR(50),
            Genre VARCHAR(128),
            PRIMARY KEY(ID)
        );
        '''
        SqlDB.sql_query(query_init, db_table, drop, UserSettings.use_sqlite3)

class BookStoreEntry:

    def __init__(self, store_entry: LibraryEntry, db_id = None):
        self.entry = store_entry
        self.db_id = db_id

    def __repr__(self):
        typed_out = f"ID: {self.db_id}\n"
        typed_out += f"{self.entry}"
        return typed_out

    @staticmethod
    def get_entry():
        new_lib_entry = LibraryEntry.get_entry()
        # next_id = SqlDB.get_last_id(BookStore.db_table, UserSettings.use_sqlite3) + 1
        book_store_entry = BookStoreEntry(new_lib_entry)
        return book_store_entry

    def save_to_db(self, table = BookStore.db_table):
        insert_query = f"""
        INSERT INTO {table} (ID, Name, Author, Quantity, Available)
        VALUES ({self.db_id}, "{self.entry.book.name}", "{self.entry.book.author}", {self.entry.quantity}, {self.entry.available});
        """
        SqlDB.sql_query(insert_query, table, use_sqlite3=UserSettings.use_sqlite3)
        print(f"Book added! \"{self.entry.book.name}\" has been saved to database")
        print()
        return self
