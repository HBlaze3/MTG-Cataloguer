from json import load, dump
from os import remove, listdir
from os.path import exists, join
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
    def save_file(file_path, data, mode='wb'):
        with open(file_path, mode) as file:
            file.write(data)
    
    @staticmethod
    def write_metadata(file_path, metadata, mode='r+'):
        with open(file_path, mode, encoding='utf-8') as meta_file:
            meta_file.write(f"{metadata}\n")

    @staticmethod
    def download_file(url, save_as, override, step=None):
        def fetch_response():
            response = get(url[0] if save_as == "all_cards.json" else url, stream=True)
            response.raise_for_status()
            return response
        
        try:
            response = fetch_response()
            last_modified = response.headers.get('Last-Modified')

            def download_and_save():
                if save_as == "all_cards.json":
                    Startup.process_all_cards(response, save_as, url[1])
                else:
                    Startup.process_other_files(response, save_as, last_modified)

            if override or not exists(save_as) or Startup.date_check(save_as, url[1] if save_as == "all_cards.json" else last_modified):
                download_and_save()

        except Exception as e:
            print(f"Error downloading {save_as}: {e}")

    @staticmethod
    def process_all_cards(response, save_as, date):
        with Startup.get_gzip_file(response) as gzip_file:
            Startup.write_metadata(save_as, date, 'w')
            with open(save_as, 'r+', encoding='utf-8') as file:
                file.readline()
                file.write('[\n')
                first = True

                for card in items(gzip_file, 'item'):
                    processed_card = Startup.create_processed_card(card)
                    if not first:
                        file.write(',\n')
                    first = False
                    dump(processed_card, file)

                file.write('\n]')
        from MainWindow import MainWindow
        MainWindow.reload_all_cards()

    @staticmethod
    def get_gzip_file(response):
        if 'Content-Encoding' in response.headers and response.headers['Content-Encoding'] == 'gzip':
            return GzipFile(fileobj=response.raw)
        content = response.raw.read(2)
        response.raw.seek(0)
        if content == b'\x1f\x8b':
            return GzipFile(fileobj=response.raw)
        return response.raw

    @staticmethod
    def process_other_files(response, save_as, last_modified):
        if ".zip" in save_as:
            Startup.write_metadata(save_as[:-4] + ".meta", last_modified)
            Startup.save_file(save_as, response.raw.read())
            Startup.extract_zip(save_as)
        else:
            if Startup.get_gzip_file(response):
                with Startup.get_gzip_file(response) as gzip_file:
                    Startup.save_file(save_as, gzip_file.read(), mode='wb')
            else:
                Startup.save_file(save_as, response.raw.read())
            if save_as == "DeckList.json":
                Startup.process_deck_list(save_as, last_modified)
            else:
                Startup.write_metadata(save_as, last_modified)

    @staticmethod
    def process_deck_list(save_as, last_modified):
        deck_data = []
        with open(save_as, 'r+', encoding='utf-8') as f:
            data = load(f)
            for deck in data['data']:
                deck_info = {
                    "name": f"{deck['name']} {deck['code']}",
                    "fileName": f"{deck['fileName']}.json"
                }
                deck_data.append(deck_info)
            f.seek(0)
            f.write(f"{last_modified}\n")
            dump(deck_data, f)
            f.truncate()
        from MainWindow import MainWindow
        MainWindow.reload_DeckList()

    @staticmethod
    def create_processed_card(card):
        return {
            "lang": card.get("lang"),
            "release_date": card.get("released_at"),
            "name": card.get("name"),
            "type_line": card.get("type_line"),
            "color_identity": ",".join(card.get("color_identity", [])),
            "set_name": card.get("set_name"),
            "set": card.get("set"),
            "collector_number": card.get("collector_number"),
            "usd": card.get("prices", {}).get("usd"),
            "usd_foil": card.get("prices", {}).get("usd_foil"),
        }
    
    @staticmethod
    def extract_zip(zip_File):
        unzipped = "./"+zip_File[:-4]
        try:
            with zipfile.ZipFile(zip_File, 'r') as zip_ref:
                zip_ref.extractall(unzipped)
        finally:
            if exists(zip_File):
                remove(zip_File)
            if unzipped == './AllDeckFiles':
                Startup.rewrite_json([join(unzipped, file) for file in listdir(unzipped)])

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
    def get_language_code(lang):
        match lang:
            case "English":
                return "en"
            case "Spanish":
                return "es"
            case "French":
                return "fr"
            case "German":
                return "de"
            case "Italian":
                return "it"
            case "Portuguese (Brazil)":
                return "pt"
            case "Japanese":
                return "ja"
            case "Korean":
                return "ko"
            case "Russian":
                return "ru"
            case "Chinese Simplified":
                return "zhs"
            case "Chinese Traditional":
                return "zht"
            case "Phyrexian":
                return "ph"

    @staticmethod
    def create_card_data_dict(card_info):
        quantity = str(card_info['count'])
        if card_info['isFoil'] == True:
            quantity_foil = quantity
        else:
            quantity_foil = ""
        return {
            "lang": Startup.get_language_code(card_info['language']),
            "release_date": "",
            "name": card_info['name'],
            "type_line": card_info['type'],
            "color_identity": ','.join(card_info['colorIdentity']),
            "set_name": "",
            "set": card_info['setCode'],
            "collector_number": card_info['number'],
            "quantity": quantity,
            "quantity_foil": quantity_foil,
            "usd": "",
            "usd_foil": "",
            "total_usd": "",
            "total_usd_foil": "",
            "storage_areas": "N/A",
            "storage_quantity": quantity,
            "deck_type": "",
            "deck_quantity": "",
            "deck_type_two": "",
            "deck_quantity_two": "",
            "deck_type_three": "",
            "deck_quantity_three": "",
            "deck_type_four": "",
            "deck_quantity_four": ""
        }