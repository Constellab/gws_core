import reflex as rx

# Map of file extensions (uppercase) to display colors
_EXTENSION_COLORS: dict[str, str] = {
    # PDF
    "PDF": "#DC2626",
    # Word
    "DOC": "#2B579A",
    "DOCX": "#2B579A",
    "ODT": "#2B579A",
    # Excel
    "XLS": "#217346",
    "XLSX": "#217346",
    "CSV": "#217346",
    "ODS": "#217346",
    # PowerPoint
    "PPT": "#D24726",
    "PPTX": "#D24726",
    "ODP": "#D24726",
    # Images
    "PNG": "#9333EA",
    "JPG": "#9333EA",
    "JPEG": "#9333EA",
    "GIF": "#9333EA",
    "SVG": "#9333EA",
    "WEBP": "#9333EA",
    # Archives
    "ZIP": "#CA8A04",
    "TAR": "#CA8A04",
    "GZ": "#CA8A04",
    "RAR": "#CA8A04",
    "7Z": "#CA8A04",
    # Text / code
    "TXT": "#64748B",
    "MD": "#64748B",
    "JSON": "#0EA5E9",
    "XML": "#0EA5E9",
    "HTML": "#E34F26",
    "CSS": "#1572B6",
    "PY": "#3776AB",
    "JS": "#F7DF1E",
    "TS": "#3178C6",
}

_DEFAULT_EXTENSION_COLOR = "#64748B"


def _match_extension_color(extension: rx.Var[str]) -> rx.Var[str]:
    """Map an uppercase extension label to its color using rx.match.

    :param extension: The uppercase extension string (e.g. "PDF", "CSV")
    :return: The color hex string as a reactive Var
    """
    return rx.match(
        extension,
        *((ext, color) for ext, color in _EXTENSION_COLORS.items()),
        _DEFAULT_EXTENSION_COLOR,
    )


def extension_badge_component(extension: rx.Var[str]) -> rx.Component:
    """Create a colored badge showing a file extension (e.g. PDF, DOC, XLS).

    The extension should be an uppercase label (max 3-4 chars). The background
    color is resolved reactively via rx.match.

    :param extension: The uppercase extension label (e.g. "PDF", "CSV")
    :return: A 36x36 colored box with the extension text in white
    """
    return rx.box(
        rx.text(
            extension,
            weight="bold",
            color="white",
            trim="both",
            style={"font_size": "10px"},
        ),
        width="36px",
        height="36px",
        border_radius="var(--radius-2)",
        background=_match_extension_color(extension),
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )
