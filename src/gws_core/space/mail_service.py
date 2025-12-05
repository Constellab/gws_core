from typing import Any

from gws_core.space.space_dto import SendScenarioFinishMailData, SpaceSendMailToUsersDTO
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
        data = {"content": mail_content}

        user_id = CurrentUserService.get_and_check_current_user().id

        return cls._send_mail([user_id], subject, "generic", data)

    @classmethod
    def send_mail(cls, receivers_ids: list[str], mail_content: str, subject: str = None) -> bool:
        """Send a email to 1 or multiple users

        :param mail_content: content of the mail (supports HTML)
        :type mail_content: str
        :param subject: subject of the mail, defaults to None
        :type subject: str, optional
        :return: _description_
        :rtype: bool
        """
        data = {"content": mail_content}

        subject = f"Constellab - {subject}"

        return cls._send_mail(receivers_ids, subject, "generic", data)

    @classmethod
    def _send_mail(
        cls,
        receivers_ids: list[str],
        mail_template: str,
        subject: str = None,
        data: dict[str, Any] = None,
    ) -> bool:
        """Send an email using Space API. If success, return True, else raise an exception

        :param receivers_ids: list of user ids to send the email to
        :type receivers_ids: List[str]
        :param mail_template: the mail template to use
        :type mail_template: str
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
            receivers_ids=[user_id], mail_template="scenario-finished", data={"scenario": scenario}
        )
