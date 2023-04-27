#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sqlite3
import typing as t
from pathlib import Path


def display_trains(trains):
    """
    Вывести данные о рейсе.
    """
    # Проверить, что список поездов не пуст.
    if trains:
        line = '+-{}-+-{}-+-{}-+-{}-+'.format(
            '-' * 4,
            '-' * 30,
            '-' * 20,
            '-' * 20
        )
        print(line)
        # Заголовок таблицы.
        print(
            '| {:^4} | {:^30} | {:^20} | {:^20} |'.format(
                "№",
                "Пункт назначиния",
                "Номер поезда",
                "время отправления"
            )
        )
        print(line)
        # Вывести данные о всех поездах.
        for idx, train in enumerate(trains, 1):
            print(
                '| {:>4} | {:<30} | {:<20} |  {:<20} |'.format(
                    idx,
                    train.get('punkt_nazn', ''),
                    train.get('nomer', ''),
                    train.get('time', '')
                )
            )
        print(line)


def create_db(database_path: Path) -> None:
    """
    Создать базу данных.
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Создать таблицу с информацией о группах.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS groups (
            train_id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_title TEXT NOT NULL
        )
        """
    )

    # Создать таблицу с информацией о поездах.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            train_id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_punkt TEXT NOT NULL,
            train_nomer INTEGER NOT NULL,
            train_time LIST NOT NULL,
            FOREIGN KEY(train_id) REFERENCES groups(train_id)
        )
        """
    )

    conn.close()


def add_train(
        database_path: Path,
        punkt_nazn: str,
        nomer: int,
        time: int):
    """
    Добавить данные о поезде
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    # Получить идентификатор группы в базе данных.
    # Если такой записи нет, то добавить информацию о новой группе.
    cursor.execute(
        """
        SELECT train_nomer FROM trains WHERE group_title = ?
        """,
        (nomer,)
    )
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            """
            INSERT INTO groups (group_title) VALUES (?)
            """,
            (nomer,)
        )
        group_id = cursor.lastrowid

    else:
        group_id = row[0]

    # Добавить информацию о новом поезде.
    cursor.execute(
        """
        INSERT INTO trains (train_punkt, train_nomer, train_time)
        VALUES (?, ?, ?)
        """,
        (punkt_nazn, nomer, time)
    )

    conn.commit()
    conn.close()


def select_all(database_path: Path) -> t.List[t.Dict[str, t.Any]]:
    """
    Выбрать всех студентов.
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trains.trains_punkt, groups.group_title, trains.train_nomer
        FROM trains
        INNER JOIN groups ON groups.trains_nomer = trains.trains_nomer
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
        "punkt_nazn": row[0],
        "nomer": row[1],
        "time": row[2],
        }
        for row in rows
    ]


def select_by_num(
    database_path: Path, nomer: int
) -> t.List[t.Dict[str, t.Any]]:
    """
    Выбрать поезда с заданным номером.
    """

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trains.train_punkt, groups.group_title, trains.train_nomer
        FROM trains
        INNER JOIN groups ON groups.train_nomer = students.train_nomer
        WHERE groups.group_title = ?
        """,
        (nomer,)
    )
    rows = cursor.fetchall()

    conn.close()
    return [
        {
            "punkt_nazn": row[0],
            "nomer": row[1],
            "time": row[2],
        }
        for row in rows
    ]


def main(command_line=None):
    # Создать родительский парсер для определения имени файла.
    file_parser = argparse.ArgumentParser(add_help=False)
    file_parser.add_argument(
        "--db",
        action="store",
        required=False,
        default=str(Path.cwd() / "trains.db"),
        help="The database file name"
    )

    # Создать основной парсер командной строки.
    parser = argparse.ArgumentParser("trains")
    parser.add_argument(
        "--version",
        action="version",
        help="The main parser",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command")

    # Создать субпарсер для добавления поезда.
    add = subparsers.add_parser(
        "add",
        parents=[file_parser],
        help="Add a new train"
    )
    add.add_argument(
        "-p",
        "--punkt",
        action="store",
        required=True,
        help="punkt_nazn"
    )
    add.add_argument(
        "-n",
        "--nomer",
        type=int,
        action="store",
        help="The trains num"
    )
    add.add_argument(
        "-t",
        "--time",
        type=int,
        action="store",
        required=True,
        help="The train time"
    )

    # Создать субпарсер для отображения всех поездов.
    _ = subparsers.add_parser(
        "display",
        parents=[file_parser],
        help="Display all trains"
    )

    # Создать субпарсер для выбора поездов.
    select = subparsers.add_parser(
        "select",
        parents=[file_parser],
        help="Select the train"
    )
    select.add_argument(
        "-s",
        "--select",
        action="store",
        required=True,
        help="The required select"
    )

    # Выполнить разбор аргументов командной строки.
    args = parser.parse_args(command_line)

    # Получить путь к файлу базы данных.
    db_path = Path(args.db)
    create_db(db_path)

    # Добавить поезд.

    if args.command == "add":
        add_train(db_path, args.punkt_nazn, args.nomer, args.time)

    # Отобразить все поезда.
    elif args.command == "display":
        display_trains(select_all(db_path))

    # Выбрать требуемый поезд.
    elif args.command == "select":
        display_trains(select_by_num(db_path, args.select))
        pass


if __name__ == '__main__':
    main()