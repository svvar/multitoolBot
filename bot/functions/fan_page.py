import secrets
import string

import faker
import aiohttp
import asyncio
import bs4

adjectives = [
    "Amazing", "Awesome", "Bright", "Brilliant", "Creative", "Dynamic", "Energetic",
    "Epic", "Excellent", "Fantastic", "Future", "Global", "Great", "Innovative",
    "Inspiring", "Leading", "Majestic", "Modern", "Outstanding", "Pioneering",
    "Remarkable", "Smart", "Spectacular", "Stellar", "Superb", "Tech", "Visionary",
    "Wise", "Bold", "Clever", "Daring", "Eager", "Fearless", "Gallant",
    "Heroic", "Intrepid", "Keen", "Lively", "Mighty", "Noble", "Plucky",
    "Quick", "Resolute", "Spirited", "Tenacious", "Valiant", "Zesty", "Advanced",
    "Astounding", "Avant-garde", "Cutting-edge", "Distinctive", "Elite", "Eminent",
    "Exemplary", "Formidable", "Groundbreaking", "Illustrious", "Ingenious",
    "Innovative", "Legendary", "Luminary", "Masterful", "Premier", "Prominent",
    "Renowned", "Resourceful", "Revolutionary", "Skillful", "Sleek", "Sophisticated",
    "Trailblazing", "Unparalleled", "Virtuoso", "Visionary", "Vivid", "Zealous"
]

nouns = [
    "Hub", "Space", "Club", "Zone", "Network", "Center", "World", "Society",
    "Community", "Group", "Alliance", "Circle", "Forum", "League", "Foundation",
    "Initiative", "Project", "Program", "Ventures", "Enterprises", "Studio",
    "Lab", "Academy", "Institute", "Platform", "Nexus", "Base", "Core", "Unit",
    "Union", "Workshop", "Guild", "House", "Arena", "Arena", "Field", "Sector",
    "Domain", "Territory", "Realm", "Sphere", "Area", "Quarter", "Station",
    "Port", "Harbor", "Nest", "Pavilion", "Haven", "Sanctuary", "Refuge",
    "Retreat", "Sanctum", "Oasis", "Den", "Chamber", "Cove", "Depot", "Warehouse",
    "Storehouse", "Reservoir", "Repository", "Archive", "Vault", "Library",
    "Collection", "Gallery", "Exhibit", "Museum", "Hall", "Parlor", "Showroom",
    "Exposition", "Display", "Workshop", "Studio", "Salon", "Boutique", "Shop",
    "Market", "Mart"
]

prefixes = [
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "",
    "The", "Ultra", "Mega", "Super", "Hyper", "Neo", "Pro", "Prime",
    "Omni", "Aero", "Aqua", "Auto", "Bio", "Cyber", "Eco", "Electro",
    "Geo", "Info", "Macro", "Quantum"
]

suffixes = [
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "", "", "",
    "Initiative", "Project", "Program", "Ventures", "Enterprises", "Solutions",
    "Systems", "Dynamics", "Concepts", "Technologies", "Innovations", "Creations",
    "Designs", "Services", "Productions", "Works", "Labs", "Studios", "Works", "Industries"
]

address_generator_url = "https://generatefakename.com/ru/address"


def generate_fan_page_names(n_names=20):
    fake = faker.Faker()
    names = []

    for _ in range(n_names):
        adjective = fake.word(ext_word_list=adjectives)
        noun = fake.word(ext_word_list=nouns)
        prefix = fake.word(ext_word_list=prefixes)
        suffix = fake.word(ext_word_list=suffixes)

        names.append(f"{prefix} {adjective} {noun} {suffix}".strip())

    return names


async def generate_addresses(lang_code, n_addresses):
    url = f"{address_generator_url}/{lang_code.split('_')[0].lower()}/{lang_code.split('_')[1].lower()}"
    connector = aiohttp.TCPConnector(limit=4)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [_address_request(session, url) for _ in range(n_addresses)]
        addresses = await asyncio.gather(*tasks)
        return [a.replace('\n', ' ') for a in addresses]



async def _address_request(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            soup = bs4.BeautifulSoup(await response.text(), 'html.parser')
            address = soup.find('div', class_='panel-body').find('h3')
            return address.text
        return None


def generate_phones(lang_code, n_numbers):
    fake = faker.Faker(lang_code)

    phones = []
    for i in range(n_numbers):
        phone = fake.phone_number()
        phones.append(phone)

    return phones


def password_gen(n_chars: int, special_chars: bool, letters: bool, uppercase: bool, n_passwords: int):
    alphabet = string.digits
    if letters:
        alphabet += string.ascii_lowercase
    if uppercase:
        alphabet += string.ascii_uppercase
    if special_chars:
        alphabet += string.punctuation

    passwords = []

    for _ in range(n_passwords):
        password = ''.join(secrets.choice(alphabet) for _ in range(n_chars))
        passwords.append(password)

    return passwords


def generate_names_task(gender, locale, amount):
    fake = faker.Faker(locale=locale)
    names = []

    for _ in range(amount):
        if gender == 'male':
            names.append(f'`{fake.first_name_male()} {fake.last_name_male()}`\n')
        elif gender == 'female':
            names.append(f'`{fake.first_name_female()} {fake.last_name_female()}`\n')
        else:
            names.append(f'`{fake.first_name()} {fake.last_name()}`\n')

    return names



async def main():
    addresses = await generate_addresses('uk_UA', 10)
    print(addresses)

if __name__ == '__main__':
    asyncio.run(main())


