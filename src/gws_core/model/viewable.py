# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Union

from gws_core.core.decorator.transaction import Transaction
from peewee import ModelSelect

from ..comment.comment import Comment
from ..core.model.model import Model
from .view_model import ViewModel


class Viewable(Model):
    """
    Viewable class.
    """

    # -- A --
    # todo fix type
    def add_comment(self, message: str, reply_to: Comment = None) -> Comment:
        """
        Add a new comment to this object

        :param message: The comment message
        :type message: `str`
        :param reply_to: The comment to reply to
        :type reply_to: `Comment`
        :returns: The added comment
        :rtype: `Comment`
        """

        if not self.id:
            self.save()

        comment: Comment = None
        if reply_to:
            comment = Comment(
                object_uri=self.uri,
                object_typing_name=self._typing_name,
                reply_to=reply_to
            )
        else:
            comment = Comment(
                object_typing_name=self._typing_name,
                object_uri=self.uri,
            )

        comment.set_message(message)
        comment.save()
        return comment

    @Transaction()
    def archive(self, archive: bool) -> 'Viewable':
        """
        Archive of Unarchive Viewable and all its ViewModels

        :param tf: True to archive, False to unarchive
        :type tf: `bool`
        :return: True if sucessfully done, False otherwise
        :rtype: `bool`
        """

        if self.is_archived == archive:
            return True

        query: List[ViewModel] = ViewModel.select().where(
            (ViewModel.model_uri == self.uri) &
            (ViewModel.is_archived == (not archive))
        )

        for view_model in query:
            view_model.archive(archive)

        return super().archive(archive)

    # -- C --

    @property
    def comments(self) -> list:
        """
        Returns the list of comments of this object
        """

        return Comment.select()\
            .where(Comment.object_uri == self.uri)\
            .order_by(Comment.creation_datetime.desc())

    def create_view_model(self, data: dict = {}) -> 'ViewModel':
        """
        Create a ViewModel

        :param data: The rendering data
            * render: `str`, the name of the rendering function (e.g. if `render = as_csv`, the method `view__as_csv()` of the `model`.)
            * params: `dict`, the parameters passed to the rendering function
            * metadata: `dict`, supplementatry metadata
        :type data: `dict`
        """

        if not isinstance(data, dict):
            data = {}
        view_model = ViewModel(model=self)
        view_model.update(data, track_activity=False)
        return view_model

    # -- D --

    # -- G --

    # -- R --

    def render__as_json(self, **kwargs) -> Union[str, dict]:
        """
        Renders the model as a JSON string or dictionnary. This method is used by :class:`ViewModel` to create view rendering.

        :param kwargs: Parameters passed to the method :meth:`to_json`.
        :type kwargs: `dict`
        :return: The view representation
        :rtype: `dict`, `str`
        """

        return self.to_json(**kwargs)

    # -- S --

    # -- V --

    def view(self, data: dict = None) -> dict:
        """
        Renders a ViewModel

        :param data: The rendering data
            * func: the name of rendering function to use (e.g. if `func = csv`, the method `view__as_csv( **kwargs )` of the model with be used if it is defined)
            * params: the parameters passed to the rendering function as `kwargs`
        :type params: `dict`
        """

        if data is None:
            data = {}

        if not isinstance(data, dict):
            data = {}
        view_model = self.create_view_model(data)
        return view_model.render()

    @property
    def view_models(self):
        """
        Get all the ViewModels of the Viewable
        """
        return ViewModel.select().where(ViewModel.model_uri == self.uri)
