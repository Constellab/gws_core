from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class HtmlStyle:
    """Represents an external stylesheet link."""

    href: str
    attributes: dict = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class HtmlScript:
    """Represents an external script."""

    src: str
    attributes: dict = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class HtmlBody:
    """Represents the body content with separated components."""

    links: list["HtmlLink"]  # Links in the body (modulepreload, etc.)
    scripts: list["HtmlScript"]  # External scripts in the body
    content: str  # The remaining HTML content (excluding links and scripts)
    attributes: dict = None  # Body tag attributes

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class HtmlLink:
    """Represents a link element (modulepreload, preload, etc.)."""

    href: str
    rel: str
    attributes: dict = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class ParsedHtml:
    """Container for parsed HTML components."""

    head_styles: list[HtmlStyle]  # External stylesheets from <head>
    body: HtmlBody  # Body content with links, scripts, and HTML


class AppPluginHtmlParser:
    """Parser to read and extract css links and script from an index.html file of a plugin.
    The plugin is generated from angular build. This is used to extract the resources to be
    loaded in another html file (streamlit) or in a javascript file (reflex).

    Only extracts external (relative) resources, ignoring inline styles and scripts.
    """

    def __init__(self, relative_path_prefix: str = ""):
        """
        Initialize the HTML parser.

        Args:
            relative_path_prefix: The prefix to add to relative paths in href and src attributes
        """
        self.relative_path_prefix = relative_path_prefix

    def is_relative_path(self, path: str) -> bool:
        """
        Check if a path is relative (not absolute URL).

        Args:
            path: The path to check

        Returns:
            True if the path is relative, False otherwise
        """
        if not path:
            return False

        # Absolute URLs start with http://, https://, //, mailto:, #, etc.
        if path.startswith(("http://", "https://", "//", "mailto:", "#", "data:", "javascript:")):
            return False

        return True

    def replace_relative_path(self, original_path: str) -> str:
        """
        Replace relative paths with a prefixed path.

        Args:
            original_path: The original path from href or src attribute

        Returns:
            The path with prefix applied if it's a relative path
        """
        if not original_path:
            return original_path

        # Skip absolute URLs
        if not self.is_relative_path(original_path):
            return original_path

        # Normalize the original path - remove leading ./
        normalized_path = original_path[2:] if original_path.startswith("./") else original_path

        # If prefix is empty, return the normalized path
        if not self.relative_path_prefix:
            return normalized_path

        # If prefix ends with '/', just concatenate
        if self.relative_path_prefix.endswith("/"):
            return self.relative_path_prefix + normalized_path

        # Otherwise add a '/' separator
        return self.relative_path_prefix + "/" + normalized_path

    def parse(self, html_content: str) -> ParsedHtml:
        """
        Parse HTML content and extract external styles and scripts.

        Args:
            html_content: The HTML content as a string

        Returns:
            ParsedHtml object containing extracted components
        """
        soup = BeautifulSoup(html_content, "html.parser")

        head_styles = self._extract_styles(soup)
        body = self._extract_body(soup)

        return ParsedHtml(head_styles=head_styles, body=body)

    def _extract_styles(self, soup: BeautifulSoup) -> list[HtmlStyle]:
        """
        Extract only external stylesheet links from the HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of HtmlStyle objects (only external stylesheets)
        """
        styles = []

        # Extract only <link rel="stylesheet"> tags with relative paths
        for link_tag in soup.find_all("link", {"rel": "stylesheet"}):
            # Skip if within noscript
            if link_tag.parent and link_tag.parent.name == "noscript":
                continue

            original_href = link_tag.get("href", "")

            # Only include relative paths
            if not self.is_relative_path(original_href):
                continue

            processed_href = self.replace_relative_path(original_href)
            attributes = {k: v for k, v in link_tag.attrs.items() if k not in ["href", "rel"]}

            styles.append(HtmlStyle(href=processed_href, attributes=attributes))

        return styles

    def _extract_body(self, soup: BeautifulSoup) -> HtmlBody:
        """
        Extract body content from the HTML, separating links and external scripts.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            HtmlBody object with separated components
        """
        if not soup.body:
            return HtmlBody(links=[], scripts=[], content="", attributes={})

        # Clone the body to avoid modifying the original
        body_copy = BeautifulSoup(str(soup.body), "html.parser").body

        # Remove noscript tags
        for noscript in body_copy.find_all("noscript"):
            noscript.decompose()

        # Extract links from body (only relative paths)
        body_links = []
        for link_tag in body_copy.find_all("link"):
            rel = link_tag.get("rel")
            if not rel:
                continue

            # Convert rel to string if it's a list
            rel_str = rel[0] if isinstance(rel, list) else rel

            # Skip stylesheets as they should be in head
            if rel_str == "stylesheet":
                continue

            original_href = link_tag.get("href", "")

            # Only include relative paths
            if not self.is_relative_path(original_href):
                link_tag.decompose()
                continue

            processed_href = self.replace_relative_path(original_href)
            attributes = {k: v for k, v in link_tag.attrs.items() if k not in ["href", "rel"]}

            body_links.append(HtmlLink(href=processed_href, rel=rel_str, attributes=attributes))

            # Remove the link tag from body_copy
            link_tag.decompose()

        # Extract only external scripts from body (only relative paths)
        body_scripts = []
        for script_tag in body_copy.find_all("script"):
            src = script_tag.get("src")

            # Skip inline scripts
            if not src:
                script_tag.decompose()
                continue

            # Only include relative paths
            if not self.is_relative_path(src):
                script_tag.decompose()
                continue

            processed_src = self.replace_relative_path(src)
            attributes = {k: v for k, v in script_tag.attrs.items() if k not in ["src"]}

            body_scripts.append(HtmlScript(src=processed_src, attributes=attributes))

            # Remove the script tag from body_copy
            script_tag.decompose()

        # Process all remaining href attributes
        for element in body_copy.find_all(href=True):
            if self.is_relative_path(element["href"]):
                element["href"] = self.replace_relative_path(element["href"])

        # Process all remaining src attributes
        for element in body_copy.find_all(src=True):
            if self.is_relative_path(element["src"]):
                element["src"] = self.replace_relative_path(element["src"])

        # Get the inner HTML (body content without the body tag itself, and without links/scripts)
        body_content = "".join(str(child) for child in body_copy.children)

        # Extract body attributes
        body_attributes = {k: v for k, v in soup.body.attrs.items()}

        return HtmlBody(
            links=body_links, scripts=body_scripts, content=body_content, attributes=body_attributes
        )
