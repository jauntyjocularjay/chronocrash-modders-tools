#!/usr/bin/env python3
"""
Générateur d'encadrés ASCII/Unicode pour titres dans le code.
"""

from enum import Enum


class BoxStyle(Enum):
    UNICODE = "unicode"      # ╔═╗║╚╝
    BLOCK = "block"          # █▀▄
    BLOCK_INVERSE = "block_inverse"  # █▌▐
    ASCII = "ascii"          # +-|


# Caractères pour chaque style
STYLES = {
    BoxStyle.UNICODE: {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "h": "═", "v": "║"
    },
    BoxStyle.BLOCK: {
        "top": "▄", "bottom": "▀", "v": "█"
    },
    BoxStyle.BLOCK_INVERSE: {
        "fill": "█", "vl": "▌", "vr": "▐"
    },
    BoxStyle.ASCII: {
        "tl": "+", "tr": "+", "bl": "+", "br": "+",
        "h": "-", "v": "|"
    },
}


def generate_title_box(
    title: str,
    prefix: str = "#",
    style: BoxStyle = BoxStyle.UNICODE,
    width: int | None = None,
    padding: int = 6,
    margin: int = 0
) -> str:
    """
    Génère un encadré pour un titre.

    Args:
        title: Le texte du titre
        prefix: Préfixe de commentaire (#, //, --, etc.)
        style: Style de l'encadré (BoxStyle.UNICODE, BLOCK, BLOCK_INVERSE, ASCII)
        width: Largeur totale (sans préfixe). None = auto basé sur le titre
        padding: Espaces de chaque côté du titre (ignoré si width est défini)
        margin: Espaces entre le préfixe de commentaire et l'encadré (pour centrer)

    Returns:
        String multi-lignes de l'encadré
    """
    # Calcul de la largeur intérieure
    if width is None:
        inner_width = len(title) + (padding * 2)
    else:
        inner_width = width - 2  # -2 pour les bordures

    # Centrage du titre
    centered_title = title.center(inner_width)

    # Préfixe avec espace et marge
    margin_str = " " * margin
    p = f"{prefix} {margin_str}" if prefix else margin_str

    chars = STYLES[style]
    lines = []

    if style == BoxStyle.UNICODE or style == BoxStyle.ASCII:
        # Ligne du haut
        lines.append(f"{p}{chars['tl']}{chars['h'] * inner_width}{chars['tr']}")
        # Ligne du titre
        lines.append(f"{p}{chars['v']}{centered_title}{chars['v']}")
        # Ligne du bas
        lines.append(f"{p}{chars['bl']}{chars['h'] * inner_width}{chars['br']}")

    elif style == BoxStyle.BLOCK:
        full_width = inner_width + 2  # +2 pour les █ latéraux
        # Ligne du haut
        lines.append(f"{p}{chars['top'] * full_width}")
        # Ligne du titre
        lines.append(f"{p}{chars['v']}{centered_title}{chars['v']}")
        # Ligne du bas
        lines.append(f"{p}{chars['bottom'] * full_width}")

    elif style == BoxStyle.BLOCK_INVERSE:
        full_width = inner_width + 4  # +4 pour █▌ et ▐█
        # Ligne du haut
        lines.append(f"{p}{chars['fill'] * full_width}")
        # Ligne du titre
        lines.append(f"{p}{chars['fill']}{chars['vl']}{centered_title}{chars['vr']}{chars['fill']}")
        # Ligne du bas
        lines.append(f"{p}{chars['fill'] * full_width}")

    return "\n".join(lines)


def print_title_box(title: str, **kwargs) -> None:
    """Génère et affiche un encadré."""
    print(generate_title_box(title, **kwargs))


# --- Raccourcis pratiques ---

def py_title(title: str, style: BoxStyle = BoxStyle.UNICODE, **kwargs) -> str:
    """Encadré pour Python (#)"""
    return generate_title_box(title, prefix="#", style=style, **kwargs)


def js_title(title: str, style: BoxStyle = BoxStyle.UNICODE, **kwargs) -> str:
    """Encadré pour JavaScript/C (//)"""
    return generate_title_box(title, prefix="//", style=style, **kwargs)


def sql_title(title: str, style: BoxStyle = BoxStyle.UNICODE, **kwargs) -> str:
    """Encadré pour SQL (--)"""
    return generate_title_box(title, prefix="--", style=style, **kwargs)


def lua_title(title: str, style: BoxStyle = BoxStyle.UNICODE, **kwargs) -> str:
    """Encadré pour Lua (--)"""
    return generate_title_box(title, prefix="--", style=style, **kwargs)


# --- Demo ---

if __name__ == "__main__":
    title = "Configuration Database"

    print("=" * 60)
    print("STYLE: Unicode Box")
    print("=" * 60)
    print("\nPython:")
    print(py_title(title, BoxStyle.UNICODE))
    print("\nJavaScript:")
    print(js_title(title, BoxStyle.UNICODE))

    print("\n" + "=" * 60)
    print("STYLE: Bloc plein")
    print("=" * 60)
    print("\nPython:")
    print(py_title(title, BoxStyle.BLOCK))
    print("\nJavaScript:")
    print(js_title(title, BoxStyle.BLOCK))

    print("\n" + "=" * 60)
    print("STYLE: Bloc plein inversé")
    print("=" * 60)
    print("\nPython:")
    print(py_title(title, BoxStyle.BLOCK_INVERSE))
    print("\nJavaScript:")
    print(js_title(title, BoxStyle.BLOCK_INVERSE))

    print("\n" + "=" * 60)
    print("STYLE: ASCII classique")
    print("=" * 60)
    print("\nPython:")
    print(py_title(title, BoxStyle.ASCII))

    print("\n" + "=" * 60)
    print("OPTIONS: Largeur fixe (60) et padding custom")
    print("=" * 60)
    print("\nLargeur fixe 60:")
    print(py_title("Court", BoxStyle.UNICODE, width=60))
    print(py_title("Un titre beaucoup plus long", BoxStyle.UNICODE, width=60))

    print("\nPadding minimal (2):")
    print(py_title(title, BoxStyle.UNICODE, padding=2))

    print("\nSans préfixe:")
    print(generate_title_box(title, prefix="", style=BoxStyle.UNICODE))
