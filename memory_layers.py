# memory_layers.py

def load(path: str) -> str:
    with open(f"lore/{path}", encoding="utf-8") as f:
        return f.read().strip()

BIO_SHAO = load("Shao.txt")
ALLEY = load("Alleyway.txt")
AZUKI_WORLD = "\n".join([
    load("Azuki nft.txt"),
    load("Elementals.txt"),
    load("Garden.txt")
])
BEANZ_LORE = "\n".join([
    load("BEANZ nft.txt"),
    load("Beanz.txt")
])
HILUMIA = load("Hilumia.txt")
MYTHS = load("Myths of the Garden.txt")
