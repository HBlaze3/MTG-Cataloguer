from json import dump
from os import remove
from os.path import exists
from gzip import GzipFile
import zipfile
from ijson import items
from requests import get
from scrython.sets import Sets
from PyQt5.QtCore import QThread

class WorkerThread(QThread):
    def __init__(self, target, args=(), kwargs=None):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}

    def run(self):
        self.target(*self.args, **self.kwargs)

class Startup:
    @staticmethod
    def startup_tasks(override=False):
        tasks = [
            WorkerThread(target=Startup.fetch_sets, args=(Sets().data(), override,)),
            WorkerThread(target=Startup.download_file, args=(
                Startup.get_bulk_data_url(), 
                "all_cards.json", 
                override,
                1,
            )),
            WorkerThread(target=Startup.download_file, args=(
                "https://mtgjson.com/api/v5/AllDeckFiles.zip", 
                "AllDeckFiles.zip",
                override,
                2,
            )),
            WorkerThread(target=Startup.download_file, args=(
                "https://mtgjson.com/api/v5/DeckList.json", 
                "DeckList.json",
                override,
                3,
            ))
        ]

        for task in tasks:
            task.start()
            
        for task in tasks:
            task.wait()

    @staticmethod
    def date_check(filename, recent_date):
        try:
            if ".zip" in filename:
                filename = filename[:-4]+".meta"
            with open(filename, 'r') as file:
                stored_date = file.readline().strip()
                if stored_date == recent_date:
                    return False
        except (FileNotFoundError, KeyError):
            return True
        
    @staticmethod
    def fetch_sets(sets_data, override):
        def save_sets():
            sets = [s['code'] for s in sets_data if not s['digital']]
            with open(filename, 'w') as file:
                file.write(f"{recent_date}\n")
                dump(sets, file)
            from MainWindow import MainWindow
            MainWindow.reload_sets()

        filename = 'sets.json'
        recent_date = max(s['released_at'] for s in sets_data if not s['digital'])

        if override:
            save_sets()
        elif exists(filename):
            if Startup.date_check(filename, recent_date):
                save_sets()
        else:
            save_sets()

    @staticmethod
    def get_bulk_data_url():
        try:
            response = get("https://api.scryfall.com/bulk-data")
            response.raise_for_status()

            bulk_data = response.json()
            for item in bulk_data['data']:
                if item['type'] == 'all_cards':
                    return [item['download_uri'], item['updated_at']]
        except Exception as e:
            return None

    @staticmethod
    def download_file(url, save_as, override, step=None):
        try:
            if save_as == "all_cards.json":
                def download_all_cards():
                    with get(url[0], stream=True) as all_cards_response:
                        all_cards_response.raise_for_status()

                        if 'Content-Encoding' in all_cards_response.headers and all_cards_response.headers['Content-Encoding'] == 'gzip':
                            gzip_file = GzipFile(fileobj=all_cards_response.raw)
                        else:
                            content = all_cards_response.raw.read(2)
                            if content == b'\x1f\x8b':
                                all_cards_response.raw.seek(0)
                                gzip_file = GzipFile(fileobj=all_cards_response.raw)
                            else:
                                all_cards_response.raw.seek(0)
                                gzip_file = all_cards_response.raw
                        with open(save_as, 'w', encoding='utf-8') as output_file:
                            output_file.write(f"{url[1]}\n")
                            output_file.write('[\n')
                            first = True

                            for card in items(gzip_file, 'item'):
                                processed_card = {
                                    "lang": card.get("lang"),
                                    "release_date": card.get("released_at"),
                                    "name": card.get("name"),
                                    "type_line": card.get("type_line"),
                                    "color_identity": card.get("color_identity"),
                                    "set_name": card.get("set_name"),
                                    "set": card.get("set"),
                                    "collector_number": card.get("collector_number"),
                                    "usd": card.get("prices", {}).get("usd"),
                                    "usd_foil": card.get("prices", {}).get("usd_foil"),
                                }

                                if not first:
                                    output_file.write(',\n')
                                first = False
                                dump(processed_card, output_file, ensure_ascii=False)

                            output_file.write('\n]')
                    from MainWindow import MainWindow
                    MainWindow.reload_all_cards()

                if override:
                    download_all_cards()
                elif exists(save_as):
                    if Startup.date_check(save_as, url[1]):
                        download_all_cards()
                else:
                    download_all_cards()
            else:
                response = get(url, stream=True)
                response.raise_for_status()
                last_modified = response.headers.get('Last-Modified')

                def save_other_files():
                    if not ".zip" in save_as:
                        with open(save_as, 'wb') as file:
                            file.write(f"{last_modified}\n".encode('utf-8'))
                            for chunk in response.iter_content(chunk_size=4096):
                                if chunk:
                                    file.write(chunk)
                        from MainWindow import MainWindow
                        MainWindow.reload_DeckList()
                    else:
                        with open(save_as[:-4] + ".meta", 'wb') as file:
                            file.write(f"{last_modified}\n".encode('utf-8'))
                        with open(save_as, 'wb') as file:
                            for chunk in response.iter_content(chunk_size=4096):
                                if chunk:
                                    file.write(chunk)
                        Startup.extract_zip(save_as)

                if override:
                    save_other_files()
                elif exists(save_as):
                    if Startup.date_check(save_as, last_modified):
                        save_other_files()
                else:
                    save_other_files()

        except Exception as e:
            pass
    
    @staticmethod
    def extract_zip(zip_File):
        try:
            with zipfile.ZipFile(zip_File, 'r') as zip_ref:
                zip_ref.extractall("./"+zip_File[:-4])
        finally:
            if exists(zip_File):
                remove(zip_File)

    @staticmethod
    def rewrite_json(file_paths):
        try:
            for file_path in file_paths:
                with open(file_path, 'r+', encoding='utf-8') as file:
                    data = items(file, 'data')
                    deck = []
                    data = list(data)[0]
                    if data['commander']:
                        commander = data['commander'][0]
                        card_data = Startup.create_card_data_dict(commander)
                        deck.append(card_data)
                    for card in data['mainBoard']:
                        card_data = Startup.create_card_data_dict(card)
                        deck.append(card_data)
                    file.seek(0)
                    dump(deck, file)
                    file.truncate()
            from MainWindow import MainWindow
            MainWindow.reload_AllDeckFiles()
        except Exception as e:
            return e
    
    @staticmethod
    def create_card_data_dict(card_info):
        return {
            "lang": card_info['language'],
            "release_date": "",
            "name": card_info['name'],
            "type_line": card_info['type'],
            "color_identity": ','.join(card_info['colorIdentity']),
            "set_name": "",
            "set": card_info['setCode'],
            "collector_number": card_info['number'],
            "quantity": card_info['count'],
            "quantity_foil": card_info.get('quantity_foil', 0),
            "usd": "",
            "usd_foil": "",
            "total_usd": "",
            "total_usd_foil": "",
            "storage_areas": "N/A",
            "storage_quantity": "",
            "deck_type": "",
            "deck_quantity": "",
            "deck_type_two": "",
            "deck_quantity_two": "",
            "deck_type_three": "",
            "deck_quantity_three": "",
            "deck_type_four": "",
            "deck_quantity_four": ""
        }