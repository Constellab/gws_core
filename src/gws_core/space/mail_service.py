from typing import Any

from gws_core.space.space_dto import (
    SendScenarioFinishMailData,
    SpaceSendMailTemplate,
    SpaceSendMailToUsersDTO,
)
from gws_core.space.space_service import SpaceService
from gws_core.user.current_user_service import CurrentUserService


class MailService:
    @classmethod
    def send_mail_to_current_user(cls, mail_content: str, subject: str) -> bool:
        """Send a email to the current connected user (or user that is running the scenario)

        :param mail_content: content of the mail (supports HTML)
        :type mail_content: str
        :param subject: subject of the mail, defaults to None
        :type subject: str, optional
        :return: _description_
        :rtype: bool
        """

        user_id = CurrentUserService.get_and_check_current_user().id

        return cls.send_mail([user_id], mail_content, subject)

    @classmethod
    def send_mail(cls, receivers_ids: list[str], mail_content: str, subject: str) -> bool:
        """Send a email to 1 or multiple users

        :param receivers_ids: list of user ids to send the email to
        :type receivers_ids: List[str]
        :param mail_content: content of the mail (supports HTML)
        :type mail_content: str
        :param subject: subject of the mail
        :type subject: str
        :return: _description_
        :rtype: bool
        """
        if not receivers_ids or len(receivers_ids) == 0:
            raise ValueError("At least one receiver id must be provided")

        if not subject:
            raise ValueError("Subject must be provided")

        if not mail_content:
            raise ValueError("Mail content must be provided")
        data = {"content": mail_content}

        subject = f"Constellab - {subject}"

        return cls._send_mail(receivers_ids, SpaceSendMailTemplate.GENERIC, subject, data)

    @classmethod
    def _send_mail(
        cls,
        receivers_ids: list[str],
        mail_template: SpaceSendMailTemplate,
        subject: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send an email using Space API. If success, return True, else raise an exception

        :param receivers_ids: list of user ids to send the email to
        :type receivers_ids: List[str]
        :param mail_template: the mail template to use
        :type mail_template: SpaceSendMailTemplate
        :param data: _description_, defaults to None
        :type data: Dict[str, Any], optional
        :param data: dynamic data for the template, defaults to None
        :type data: Dict[str, Any], optional
        :return: _description_
        :rtype: bool
        """
        mail_dto = SpaceSendMailToUsersDTO(
            receiver_ids=receivers_ids, mail_template=mail_template, data=data, subject=subject
        )

        SpaceService.get_instance().send_mail(mail_dto)

        return True

    @classmethod
    def send_scenario_finished_mail(
        cls, user_id: str, scenario: SendScenarioFinishMailData
    ) -> bool:
        return cls._send_mail(
            receivers_ids=[user_id],
            mail_template=SpaceSendMailTemplate.SCENARIO_FINISHED,
            data={"scenario": scenario},
        )
