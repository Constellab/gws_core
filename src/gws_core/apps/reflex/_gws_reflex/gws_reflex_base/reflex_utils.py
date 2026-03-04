from typing import Any


class ReflexTheme:
    """
    Theme color constants for Reflex components.
    The color schemes are overriden in the style.css of the main Reflex app.
    """

    ACCENT = "accent"
    SECONDARY = "violet"
    TERTIARY = "pink"


class ReflexUtils:
    @staticmethod
    def multiline_ellipsis_css(lines: int, max_width: str = "100%") -> dict[str, Any]:
        """Utility function to generate CSS styles for multiline text ellipsis.


        Args:
            lines (int): The number of lines to display before truncating.
            max_width (str, optional): The maximum width of the text container. Defaults to "100%".

        Returns:
            Dict[str, Any]: A dictionary containing the CSS styles for multiline text ellipsis.

        Example:
            ```python
            "This is a long text that should be truncated after a few lines.",
            style=ReflexUtils.multiline_ellipsis_css(lines=3, max_width="300px")
            )
            ```
        """
        return {
            "overflow": "hidden",
            "display": "-webkit-box",
            "-webkit-line-clamp": lines,
            "-webkit-box-orient": "vertical",
            "max-width": max_width,
        }
