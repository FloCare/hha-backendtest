from django.conf import settings

import logging

logger = logging.getLogger(__name__)


class PubnubService:
    def __init__(self):
        pass

    @staticmethod
    def publish(channel, message):
        settings.PUBNUB.publish().channel(channel).message(message).async(my_publish_callback)

    @staticmethod
    def get_organization_channel(organization):
        return 'organisation_' + str(organization.uuid)

    @staticmethod
    def get_user_update_message(user):
        return {
            'actionType': 'USER_UPDATE',
            'userID': str(user.uuid)
        }


def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        logger.info("# Message successfully published to specified channel.")
    else:
        logger.error("# NOT Message successfully published to specified channel.")
        # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];
