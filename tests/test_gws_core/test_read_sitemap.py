# Generate a code that reads the sitemap.xml file and prints the number of urls

import json
import os
import re
from typing import List, TypedDict
from unittest import TestCase

import html2text
import requests
from bs4 import BeautifulSoup

from gws_core.core.utils.xml_helper import XMLHelper


class SiteMapLink(TypedDict):
    loc: str
    lastmod: str
    changefreq: str
    priority: str

# test_read_sitemap


class TestReadSiteMap(TestCase):

    info_file = 'info.json'
    sitemap_url = 'https://constellab.community/sitemap.xml'
    api_key = 'dataset-iLrNtGw051blG4ZG43lxWmrB'

    full_dataset_id = '235f7420-2e96-40e2-a5a0-09796fae9f02'

    # gws core
    gws_core_url = 'https://constellab.community/bricks/gws_core/latest/doc'
    gws_core_path = '/lab/user/bricks/gws_core/community_export/gws_core'
    gws_core_dataset_id = 'b6c4326e-b9d2-4333-9068-e0f12907f165'

    # gws academy
    gws_academy_url = 'https://constellab.community/bricks/gws_academy/latest/doc'
    gws_academy_path = '/lab/user/bricks/gws_core/community_export/gws_academy'
    gws_academy_dataset_id = '9a84c549-14e3-4df4-b52f-b4e211408092'

    def test_methods(self):
        self._load_site_map(self.gws_academy_url, self.gws_academy_path)
        self._send_all(self.gws_academy_path, self.gws_academy_dataset_id, self.api_key)

        self._load_site_map(self.gws_core_url, self.gws_core_path)
        self._send_all(self.gws_core_path, self.gws_core_dataset_id, self.api_key)

        # doc_info = {
        #     "url": "https://constellab.community/bricks/gws_academy/latest/doc/data-lab/scenario/f4453296-ccc5-4b54-8e46-2d1c2f830a0c",
        #     "title": "Scenario - gws_academy - Community",
        #     "path": "/lab/user/bricks/gws_core/community_export/gws_academy/Scenario - gws_academy - Community.md"
        # }
        # self._send_to_dify(doc_info, self.gws_academy_dataset_id, self.api_key)

    def _load_site_map(self, url: str = None, export_path: str = None) -> None:
        site_map = self._read_site_map()
        self.assertTrue(len(site_map) > 0)

        # filter urls that start with self.urls
        site_map = [link for link in site_map if link['loc'].startswith(url)]

        # remove url that contains : doc/technical-folder
        site_map = [link for link in site_map if 'doc/technical-folder' not in link['loc']]
        self.assertTrue(len(site_map) > 0)

        info = []

        progress = 0
        for link in site_map:
            result = self._download_url(link['loc'], export_path)
            info.append(result)

            progress += 1
            if progress % 5 == 0:
                print(f'Progress : {progress}/{len(site_map)}')

        with open(f'{export_path}/{self.info_file}', 'w') as f:
            f.write(json.dumps(info))

    def _download_url(self, url: str, export_path: str) -> dict:
        response = requests.get(url)

        # read the html to only keep the content of first <article> tag
        html = response.text
        start = html.find('<article')
        end = html.find('</article>') + len('</article>')
        html = html[start:end]

        # Convert HTML to Markdown
        markdown = html2text.html2text(html)

        # replace \n\n with \n
        markdown = markdown.replace('\n\n', '\n')

        markdown = markdown.replace('[Text editor\nimage]', '[Text editor image]')

        # Add URL after the title in the markdown
        markdown_lines = markdown.split('\n')
        for i, line in enumerate(markdown_lines):
            if line.startswith('#'):  # Assuming titles are marked with '# '
                header_name = line.strip('# ').strip()
                header_url = self._to_snake_case(header_name)
                full_url = f'{url}#{header_url}'
                # markdown_lines.insert(i + 1, f'[URL for section "{header_name}"]({full_url})')
                markdown_lines.insert(i + 1, f'''<!--
source_url: "{full_url}"
-->''')

        markdown = '\n'.join(markdown_lines)

       # Extract title from HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else 'No Title'

        file_path = f'{export_path}/{title}.md'
        with open(file_path, 'w') as f:
            f.write(markdown)

        return {'url': url, 'title': title, 'path': file_path}

    def _read_site_map(self) -> List[SiteMapLink]:
        xml = requests.get(self.sitemap_url)
        dict_ = XMLHelper.xml_to_dict(xml.text)
        return dict_['urlset']['url']

    # def _send(self):

    #     doc_path = '/lab/user/bricks/gws_core/community_export/4ab03b1f-a96d-4d7a-a733-ad1edf4fb53c.html'

    #     self._send_to_dify(doc_path)

    def _send_all(self, path: str, dataset_id: str, api_key: str) -> None:

        progress = 0

        info: List[dict] = None
        with open(f'{path}/{self.info_file}', 'r') as f:
            info = json.load(f)
        for doc_info in info:

            try:
                self._send_to_dify(doc_info, dataset_id, api_key)

                progress += 1
                if progress % 5 == 0:
                    print(f'Progress : {progress}/{len(info)}')
            except Exception as e:
                print(f'Error sending {doc_info["path"]} : {e}')

    def _send_to_dify(self, doc_info: dict, dataset_id: str, api_key: str) -> None:

        route = f'https://api.dify.ai/v1/datasets/{dataset_id}/document/create-by-text'

        doc_content: dict = None
        with open(doc_info['path'], 'r', encoding='UTF-8') as f:
            doc_content = f.read()

        body = {
            'name': doc_info['title'],
            'text': doc_content,
            'doc_metadata': {
                'url': doc_info['url'],
                'title': doc_info['title'],
                'language': 'en',
            },
            'doc_type': 'web_page',
            'indexing_technique': 'high_quality',
            "process_rule": {"mode": "automatic"},
            'doc_language': 'en'

        }

        headers = {
            'Authorization': 'Bearer ' + api_key,
            'Content-Type': 'application/json'
        }

        response = requests.post(route, json=body, headers=headers, timeout=5)

        if response.status_code != 200:
            print(response.json())
            raise Exception('Error sending to dify')

        # options = {
        #     "indexing_technique": "economy",
        #     "process_rule": {
        #         "rules": {
        #             "pre_processing_rules": [
        #                 {"id": "remove_extra_spaces", "enabled": True},
        #                 {"id": "remove_urls_emails", "enabled": True}
        #             ],
        #             "segmentation": {"separator": "###", "max_tokens": 500}}, "mode": "custom"}
        # }
        # data = {
        #     'data': jsonable_encoder(options)
        # }

        # files = {
        #     'file': (doc_path.split('/')[-1], open(doc_path, 'rb'), 'text/html')
        # }

        # response = requests.post(
        #     route, headers={'Authorization': 'Bearer ' + api_key},
        #     data=data, files=files, timeout=5)

    def _to_snake_case(self, text: str) -> str:
        """Convert a text to snake case
        Ex 'TestClass2Build' -> 'test_class2_build'
        """
        if text is None:
            return None

        # Replace spaces or hyphens with underscores
        text = re.sub(r'[\s\-]+', '-', text)

        # Insert underscores before uppercase letters (except the first one)
        text = re.sub(r'(?<!^)(?=[A-Z])', '-', text)

        # Convert the entire string to lowercase
        text = text.lower()

        # Remove double (or more) underscores
        text = re.sub(r'-{2,}', '-', text)

        return text
