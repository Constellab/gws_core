# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import ForeignKeyField
from gws.model import ViewModel, Experiment, Viewable

class Report(Viewable):
    experiment = ForeignKeyField(Experiment, backref="reports")
    _table_name = "report"

    def add_title(self, title: str):
        self.data["title"] = title

    def add_figure(self, model: Viewable, caption: str):
        self.data["body"].append({
           "type" : model.type,
           "uri" : model.uri,
           "caption": caption
        })

    def add_card(self, title: str, body: str):
        self.data["body"].append({
            "type": "card",
            "title": title,
            "body": body
        })

    def add_h1(self, text: str):
        self.data["body"].append({
            "type": "h1",
            "text": text,
        })

    def add_h2(self, text: str):
        self.data["body"].append({
            "type": "h2",
            "text": text,
        })

    def add_text(self, text: str):
        self.data["body"].append({
            "type": "text",
            "text": text,
        })