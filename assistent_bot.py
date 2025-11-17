from typing import Tuple, Callable, Optional, List, Dict
from functools import wraps
from collections import UserDict
from datetime import datetime, date, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):

    def __init__(self, value: str):
        self._validate(value)
        super().__init__(value)

    @staticmethod
    def _validate(value: str) -> None:
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone must contain exactly 10 digits")

    def __repr__(self) -> str:
        return f"Phone({self.value})"


class Birthday(Field):
    """
    Зберігаємо дату в єдиному полі value як date-об'єкт.
    Немає дубляжу типу value + date_value.
    """

    def __init__(self, value: str):
        try:
            dt = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        # зберігаємо date, а не сирий рядок
        super().__init__(dt)

    @property
    def date(self) -> date:
        return self.value

    def __str__(self) -> str:
        # красивий формат для виводу
        return self.value.strftime("%d.%m.%Y")

    def __repr__(self) -> str:
        return f"Birthday({self.value.strftime('%d.%m.%Y')})"


class Record:

    def __init__(self, name: str):
        self.name: Name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        phone_obj = Phone(phone)
        self.phones.append(phone_obj)

    def find_phone(self, phone: str) -> Optional[Phone]:
        for ph in self.phones:
            if ph.value == phone:
                return ph
        return None

    def remove_phone(self, phone: str) -> None:
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError("Old phone not found")

        new_phone_obj = Phone(new_phone)
        phone_obj.value = new_phone_obj.value

    def add_birthday(self, birthday_str: str) -> None:
        self.birthday = Birthday(birthday_str)

    def __str__(self) -> str:
        phones_str = "; ".join(phone.value for phone in self.phones) if self.phones else "no phones"
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"


class AddressBook(UserDict):

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> List[Dict[str, str]]:

        today = date.today()
        upcoming: List[Dict[str, str]] = []

        for record in self.data.values():
            if not record.birthday:
                continue

            bday: date = record.birthday.date
            this_year_bday = bday.replace(year=today.year)

            if this_year_bday < today:
                this_year_bday = this_year_bday.replace(year=today.year + 1)

            delta_days = (this_year_bday - today).days
            if 0 <= delta_days < 7:
                congrat_date = this_year_bday

                if congrat_date.weekday() == 5:
                    congrat_date += timedelta(days=2)
                elif congrat_date.weekday() == 6:
                    congrat_date += timedelta(days=1)

                upcoming.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congrat_date.strftime("%Y-%m-%d"),
                    }
                )

        return upcoming


def input_error(func: Callable) -> Callable:
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter arguments."
        except AttributeError:
            # коли record == None і ми звертаємось до його атрибутів
            return "Contact not found."
        except ValueError as e:
            msg = str(e).strip()
            return msg if msg else "Give me name and phone please."
    return inner


def parse_input(user_input: str) -> Tuple[str, ...]:
    parts = user_input.split()
    if not parts:
        return ("",)
    cmd, *args = parts
    cmd = cmd.strip().lower()
    return (cmd, *args)


@input_error
def add_contact(args, book: AddressBook) -> str:

    if len(args) < 2:
        raise ValueError("Give me name and phone please.")
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook) -> str:

    if len(args) == 2:
        name, new_phone = args
        record = book.find(name)
        # якщо record == None -> нижче впаде з AttributeError
        if len(record.phones) == 0:
            record.add_phone(new_phone)
            return "Contact updated."
        if len(record.phones) > 1:
            raise ValueError("Contact has several phones, use: change <name> <old_phone> <new_phone>")
        old_phone = record.phones[0].value
        record.edit_phone(old_phone, new_phone)
        return "Contact updated."
    elif len(args) == 3:
        name, old_phone, new_phone = args
        record = book.find(name)
        # якщо record == None -> AttributeError у record.edit_phone(...)
        record.edit_phone(old_phone, new_phone)
        return "Contact updated."
    else:
        raise ValueError("Give me name and phone(s) please.")


@input_error
def show_phone(args, book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    # якщо record == None -> AttributeError у record.phones
    if not record.phones:
        return "No phones."
    return "; ".join(ph.value for ph in record.phones)


@input_error
def show_all(book: AddressBook) -> str:
    if not book.data:
        return "No contacts."
    lines = []
    for record in book.data.values():
        lines.append(str(record))
    return "\n".join(lines)


@input_error
def add_birthday(args, book: AddressBook) -> str:

    if len(args) < 2:
        raise ValueError("Give me name and birthday in format DD.MM.YYYY")
    name, bday_str = args[0], args[1]
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
    record.add_birthday(bday_str)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook) -> str:

    if not args:
        raise ValueError("Enter contact name.")
    name = args[0]
    record = book.find(name)
    # якщо record == None -> AttributeError при доступі до record.birthday
    if not record.birthday:
        return "No birthday set."
    return str(record.birthday)


@input_error
def birthdays(args, book: AddressBook) -> str:

    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."

    lines = []
    for item in sorted(upcoming, key=lambda x: x["congratulation_date"]):
        lines.append(f'{item["congratulation_date"]}: {item["name"]}')
    return "\n".join(lines)


@input_error
def delete_contact(args, book: AddressBook) -> str:
    if not args:
        raise ValueError("Enter user name.")
    name = args[0]
    record = book.find(name)
    # змушуємо впасти з AttributeError, якщо контакту немає
    _ = record.name
    book.delete(name)
    return "Contact deleted."


def help_text() -> str:
    return (
        "Commands:\n"
        "  hello                              -> How can I help you?\n"
        "  add <name> <phone>                 -> Add a contact or phone to contact\n"
        "  change <name> <new> or <old> <new> -> Change phone\n"
        "  phone <name>                       -> Show phones by name\n"
        "  all                                -> Show all contacts\n"
        "  delete <name>                      -> Delete contact\n"
        "  add-birthday <name> <DD.MM.YYYY>   -> Add birthday to contact\n"
        "  show-birthday <name>               -> Show contact birthday\n"
        "  birthdays                          -> Show upcoming birthdays (next 7 days)\n"
        "  close | exit                       -> Quit\n"
    )


def main() -> None:
    book = AddressBook()
    print("Welcome to the assistant bot!")
    print("Type 'help' to see available commands.")
    while True:
        user_input = input("Enter a command: ").strip()
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "help":
            print(help_text())

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "delete":
            print(delete_contact(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "":
            continue

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
