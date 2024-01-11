from __future__ import annotations

import random

from ezpyzy.file import File


adjectives = [
    "Formidable",
    "Stalwart",
    "Euphoric",
    "Unyielding",
    "Enigmatic",
    "Hyperspace",
    "Cunning",
    "Epic",
    "Unconquerable",
    "Resilient",
    "Resolute",
    "Mystical",
    "Tenacious",
    "Daring",
    "Rogue",
    "Enthralling",
    "Uncharted",
    "Fierce",
    "Nebulous",
    "Ethereal",
    "Thunderous",
    "Serendipitous",
    "Spirited",
    "Galactic",
    "Emboldened",
    "Exotic",
    "Electric",
    "Unforgettable",
    "Infinite",
    "Supernova",
    "Mysterious",
    "Timeless",
    "Audacious",
    "Illustrious",
    "Radiant",
    "Wise",
    "Stellar",
    "Astral",
    "Relentless",
    "Luminous",
    "Intrepid",
    "Swift",
    "Enchanting",
    "Dauntless",
    "Spectral",
    "Pulsar",
    "Bewitching",
    "Elusive",
    "Fiery",
    "Regal",
    "Limitless",
    "Valiant",
    "Vibrant",
    "Dashing",
    "Exuberant",
    "Bold",
    "Dazzling",
    "Untamed",
    "Wondrous",
    "Mesmerizing",
    "Resplendent",
    "Legendary",
    "Mythical",
    "Immortal",
    "Harmonious",
    "Majestic",
    "Iconic",
    "Lively",
    "Celestial",
    "Fearless",
    "Heroic",
    "Noble",
    "Captivating",
    "Serene",
    "Charismatic"
]

starwars = [
    "Greedo",
    "Porg",
    "Athiss",
    "Nexu",
    "Jakku",
    "Kijimi",
    "Corellia",
    "Sarlacc",
    "Barriss",
    "Dengar",
    "Vandor",
    "Kuiil",
    "Anakin",
    "Utapau",
    "Manaan",
    "Reek",
    "Savage",
    "DarthMaul",
    "Mustafar",
    "Palpatine",
    "Nute",
    "Lando",
    "Bespin",
    "Jyn",
    "AhchTo",
    "DarthVader",
    "R2D2",
    "Padmé",
    "Nevarro",
    "Dxun",
    "Naboo",
    "Chirrut",
    "Paz",
    "LandosFarm",
    "Eadu",
    "Iridonia",
    "IG11",
    "Baze",
    "Wampa",
    "Cerea",
    "Hera",
    "Cantonica",
    "TatooII",
    "Han",
    "Thyferra",
    "General",
    "IG88",
    "Onderon",
    "Ponda",
    "Asajj",
    "Hapes",
    "Kanan",
    "KefBir",
    "Chewbacca",
    "Wicket",
    "Shaak",
    "Mon",
    "Moff",
    "Luke",
    "Exegol",
    "Sullust",
    "BB9E",
    "Count",
    "Lahmu",
    "Ewok",
    "YavinIV",
    "Ithor",
    "Pamarthe",
    "Ylesia",
    "Zolan",
    "DromundKaas",
    "Acklay",
    "Cassian",
    "Grievous",
    "Stewjon",
    "Ryndellia",
    "Mirial",
    "Mortis",
    "Zam",
    "Pasaana",
    "Geonosis",
    "Saw",
    "Pillio",
    "Ilum",
    "Ryloth",
    "Lothal",
    "Christophsis",
    "Atollon",
    "ClakdorVII",
    "Taris",
    "Cody",
    "Voss",
    "Boba",
    "Aayla",
    "Aurra",
    "Logray",
    "Umbara",
    "AjanKloss",
    "YagaMinor",
    "Alderaan",
    "Nien",
    "Mace",
    "Orson",
    "Kamino",
    "Zuckuss",
    "Ventress",
    "Jango",
    "Bodhi",
    "Crait",
    "Hondo",
    "Poe",
    "Ossus",
    "Kit",
    "Watto",
    "Ahsoka",
    "Sorgan",
    "Gideon",
    "Korriban",
    "Leia",
    "Rey",
    "Greef",
    "Ithorian",
    "Dantooine",
    "PolisMassa",
    "Mygeeto",
    "Mandalore",
    "Serenno",
    "Bossk",
    "ObiWan",
    "Plo",
    "Agamar",
    "CatoNeimoidia",
    "Gungan",
    "Yoda",
    "Iego",
    "Dooku",
    "Felucia",
    "Dathomir",
    "K2SO",
    "Droopy",
    "Finn",
    "NalHutta",
    "Thrawn",
    "Kashyyyk",
    "Zeb",
    "Sabine",
    "Malachor",
    "Coruscant",
    "Hoth",
    "BB8",
    "Tauntaun",
    "Rancor",
    "Jabba",
    "KiAdi",
    "Lehon",
    "DQar",
    "Tusken",
    "Dewback",
    "Krennic",
    "Jedha",
    "QuiGon",
    "Ezra",
    "Rex",
    "Bantha",
    "Aqualish",
    "Quarren",
    "Ziost",
    "C3PO",
    "Sebulba",
    "Endor",
    "Vulpter",
    "Kylo",
    "OrdMantell",
    "Wookiee",
    "Tatooine",
    "Dagobah",
    "MonCala",
    "Vardos",
    "Scarif",
    "Batuu",
    "Kessel",
    "Rishi",
    "Cad",
    "Teth",
    "Takodana"
]


def denominate(
    existing_names=None,
    parts:tuple[list[str]]=(adjectives, starwars),
    lowercase=False,
    underscores=False,
):
    if existing_names is None:
        existing_names = set()
    _ = existing_names.add
    _ = existing_names.__contains__
    while True:
        name = '_'.join(random.choice(part) for part in parts)
        if lowercase:
            name = name.lower()
        if not underscores:
            name = name.replace('_', '')
        if existing_names and name in existing_names:
            continue
        else:
            if hasattr(existing_names, 'add'):
                existing_names.add(name)
            return name











def parse_names(file):
    names = set()
    text = File(file).read()
    for line in text.split('\n'):
        if '.' in line:
            name = line.split('.', 1)[1].strip()
            names.add(name)
    return names

def clean_name(name):
    name.replace(' ', '_')
    name.replace('-', '_')
    return ''.join(c for c in name if c.isalnum() or c == '_')

def names_to_python(names):
    comma_separated = ',\n'.join(f'    "{clean_name(name)}"' for name in names)
    return f'[\n{comma_separated}\n]'

# print(names_to_python(parse_names('adjectives.txt')))


