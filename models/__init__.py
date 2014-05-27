from google.appengine.api import mail
from lib.pubnub import pubnub

__publish_key__ = 'pub-c-3d2baeb5-14e7-443b-907e-00660f6e5cd8'
__subscription_key__ = 'sub-c-9b3fe756-e594-11e3-8ffe-02ee2ddab7fe'
__secret_key__ = 'sec-c-MTVmMDJkOTctZjA5My00N2JmLWEwYjYtMWU5ODY3Yjc5MTdm'

def resuscitate_mail(heart):
    message = mail.EmailMessage(sender="alerts@heartrate-monitor.appspotmail.com",
                                subject=heart.title + " has a pulse again")

    org = heart.parent()
    if org.alert_email == '' or org.alert_email is None:
        message.to = map(lambda user: user, heart.parent().users)
    else:
        message.to = org.alert_email
    message.body = """
    Good news!

    The heart """+heart.title+""" has started to beat again.

    Check out the current state of your hearts at:
    https://heartrate-monitor.appspot.com/app/organizations/"""+str(org.key().id())+"""

    Kind regards
    https://heartrate-monitor.appspot.com/app/
    """

    try:
        message.send()
    except:
        print 'failed to send mail'
        pass

    try:
        pub = pubnub.Pubnub(
            __publish_key__,
            __subscription_key__,
            __secret_key__,
            False)
        pub.publish({
            'channel': 'remotex-alerts',
            'message': {
                'heart': heart.key().name(),
                'flatline': 'resuscitated'
            }
        })
    except:
        print ' failed to send to pubnub'
        pass


def flatline_mail(heart):
    message = mail.EmailMessage(sender="alerts@heartrate-monitor.appspotmail.com",
                                subject=heart.title + " has flatlined")

    org = heart.parent()
    if org.alert_email == '' or org.alert_email is None:
        message.to = map(lambda user: user, heart.parent().users)
    else:
        message.to = org.alert_email

    message.body = """
    Bad news!

    The heart """+heart.title+""" has not had a pulse within its threshold.

    The last pulse recieved was at """+str(heart.last_pulse)+"""

    See the heart at:
    https://heartrate-monitor.appspot.com/app/organizations/"""+str(heart.parent().key().id())+"""/hearts/"""+heart.key().name()+"""

    Check out the current state of your hearts at:
    https://heartrate-monitor.appspot.com/app/organizations/"""+str(heart.parent().key().id())+"""

    Kind regards
    https://heartrate-monitor.appspot.com/app/
    """
    try:
        message.send()
    except:
        print 'failed to send mail'
        pass
    try:
        pub = pubnub.Pubnub(
            __publish_key__,
            __subscription_key__,
            __secret_key__,
            False)
        pub.publish({
            'channel': 'remotex-alerts',
            'message': {
                'heart': heart.key().name(),
                'start': str(heart.last_pulse),
                'title': heart.title,
                'flatline': 'flatline'
            }
        })
    except:
        print 'failed to send to pubnub'
        pass


def invite_mail(invitation):
    message = mail.EmailMessage(sender="invite@heartrate-monitor.appspotmail.com",
                                subject="Invitation to "+invitation.parent().title)

    message.to = invitation.email
    message.body = """
    Hi!

    You have been invited to """+invitation.parent().title+""".

    Heartrate-monitor will keep track of scheduled tasks reporting to it. Informing you when the tasks stop reporting in within the expected time.
    Simple yet effective way to keep track that tasks are being executed.

    Respond to this invitation at:
    https://heartrate-monitor.appspot.com/app/invitations/"""+str(invitation.key())+"""


    Kind regards
    https://heartrate-monitor.appspot.com/app/
    """

    try:
        message.send()
    except:
        print 'failed to send mail'
        pass
