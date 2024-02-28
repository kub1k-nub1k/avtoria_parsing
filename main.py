import csv
import random
from time import sleep
import sqlite3
import requests
from bs4 import BeautifulSoup


def random_sleep():
    sleep(random.randint(2, 5))


def get_page_content(page: int, page_size: int = 100):
    base_url = 'https://auto.ria.com/uk/search/'
    query_params = {
        'indexName': 'auto,order_auto,newauto_search',
        'categories.main.id': '1',
        'country.import.usa.not': '-1',
        'price.currency': '1',
        'abroad.not': '0',
        'custom.not': '1',
        'page': page,
        'size': page_size,
    }

    response = requests.get(base_url, params=query_params)
    response.raise_for_status()
    return response.text


class CSVWriter:
    def __init__(self, file_name: str, headers: list):
        self.file_name = file_name

        with open(self.file_name, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    def write_data(self, data):
        with open(self.file_name, 'a') as file:
            writer = csv.writer(file)
            writer.writerow(data)


class SQLiteWriter:
    def __init__(self, db_name: str, table_name: str, headers: list):
        self.db_name = db_name
        self.table_name = table_name

        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

        create_table_query = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({', '.join(headers)})"
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def write_data(self, data):
        insert_query = f"INSERT INTO {self.table_name} VALUES ({', '.join(['?'] * len(data))})"
        self.cursor.execute(insert_query, data)
        self.connection.commit()

    def close_connection(self):
        self.connection.close()


class StdoutWriter:
    def write_data(self, data):
        print(data)


def main():
    headers = ['id', 'mark', 'model', 'year', 'link', 'price']

    writers = (
        CSVWriter('cars1.csv', headers),
        SQLiteWriter('cars.db', 'cars_table', headers),
        # StdoutWriter(),
    )

    page = 0
    while True:
        random_sleep()
        print(f"Processing page {page}!")

        page_content = get_page_content(page)

        soup = BeautifulSoup(page_content, 'html.parser')
        search_results = soup.find('div', id="searchResults")
        ticket_items = search_results.find_all("section", class_="ticket-item")

        if not ticket_items:
            print(f"No more items on page {page}!")
            break

        for ticket_item in ticket_items:
            car_details = ticket_item.find("div", class_="hide")
            car_id = car_details['data-id']
            car_mark_details = car_details['data-mark-name']
            car_model_name = car_details['data-model-name']
            car_year = car_details['data-year']

            car_link_to_view = car_details['data-link-to-view']

            detailed_page_content = requests.get(f"https://auto.ria.com{car_link_to_view}").text
            detailed_soup = BeautifulSoup(detailed_page_content, 'html.parser')
            price_element = detailed_soup.find("strong", class_="")
            car_price = price_element.text.strip() if price_element else "N/A"

            data = [car_id, car_mark_details, car_model_name, car_year, car_link_to_view, car_price]

            for writer in writers:
                writer.write_data(data)

        page += 1

    for writer in writers:
        if isinstance(writer, SQLiteWriter):
            writer.close_connection()


if __name__ == '__main__':
    main()
