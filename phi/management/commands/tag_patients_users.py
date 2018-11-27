from django.core.management.base import BaseCommand
import pandas as pd
from phi.management.commands.utils import constants
from user_auth.models import *
from phi.models import *
from django.db import transaction
from django.conf import settings

global_counter = 0


def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        print("# Message successfully published to specified channel.")
    else:
        print("# NOT Message successfully published to specified channel.")
        # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];


def send_pubnub_msg(patient, user_id, episode_id):
    global global_counter
    # SILENT NOTIFICATION
    settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
        'actionType': 'ASSIGN',
        'patientID': str(patient.uuid),
        'pn_apns': {
            "aps": {
                "content-available": 1
            },
            "payload": {
                "messageCounter": global_counter,
                "patientID": str(patient.uuid)
            },
        },
        'pn_gcm': {
            'data': {
                'notificationBody': "You have a new Patient",
                "sound": "default",
                "navigateTo": 'patient_list',
                'messageCounter': global_counter,
                'patientID': str(patient.uuid)
            }
        }
    }).async(my_publish_callback)

    # NOISY NOTIFICATION
    settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
        'pn_apns': {
            "aps": {
                "alert": {
                    "body": "You have a new Patient",
                },
                "sound": "default",
            },
            "payload": {
                "messageCounter": global_counter,
                "patientID": str(patient.uuid),
                "navigateTo": 'patient_list'
            }
        }
    }).async(my_publish_callback)

    # Message the rest of careteam
    settings.PUBNUB.publish().channel('episode_' + str(episode_id)).message({
        'actionType': 'USER_ASSIGNED',
        'userID': str(user_id),
    }).async(my_publish_callback)

    global_counter += 1


def get_user_roles(row):
    user_roles = dict()
    for role in constants.USER_ROLES:
        users = row[role]
        users = users.split('\n')
        user_list = [user.strip() for user in users]
        user_roles[role] = user_list
    return user_roles


def get_user_obj(org, user, role):
    if not user:
        return None
    name = user.split(',')
    lastname = name[0].strip()
    firstname = name[1].strip()
    try:
        access = UserOrganizationAccess.objects.get(organization=org, user__user__last_name=lastname, user__user__first_name=firstname, user_role=role)
        user = access.user.user
        return user
    except Exception as e:
        print('UserOrgAccess fetch error for user:', user, 'error:', str(e))
        return None


def _readfile(file_path):
    try:
        data = pd.read_csv(file_path, keep_default_na=False)
    except Exception as e:
        raise e
    headers = list(data.columns.values)
    print('')
    print('Headers are:', headers)
    print('')
    return data


# def my_publish_callback(envelope, status):
#     if not status.is_error():
#         print( 'Message successfully published to specified channel.')
#     else:
#         print(' NOT Message successfully published to specified channel.')
#         pass


class Command(BaseCommand):
    help = 'Tag users to patients'

    # def publish_update_message(self, user_id, patient_id):
    #     self.stdout.write('Publishing update message for ' + str(user_id) + ' - ' +  str(patient_id))
    #     settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
    #         'actionType': 'UPDATE',
    #         'patientID': patient_id,
    #     }).async(my_publish_callback)

    def add_arguments(self, parser):
        parser.add_argument('org', nargs=1, type=str)

    def process_row(self, org, row, f, g):
        patient_firstname = row.get(constants.FIRSTNAME).strip()
        patient_lastname = row.get(constants.LASTNAME).strip()
        primary_contact = row.get(constants.PHONE)
        if primary_contact:
            primary_contact = primary_contact.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')

        if (not patient_firstname) or (not patient_lastname):
            self.stderr.write('Skipping as firstname/lastname missing for patient')
            return

        self.stdout.write('Fetching patient: %s %s' % (patient_firstname, patient_lastname))
        try:
            p = Patient.objects.filter(first_name=patient_firstname).filter(last_name=patient_lastname)
            if primary_contact:
                p = p.get(primary_contact=primary_contact)
            else:
                if len(p) > 1:
                    raise Exception('Multiple records found')
                elif len(p) == 0:
                    raise Exception('No record found')
                else:
                    p = p.first()
        except Exception as e:
            f.write(patient_firstname + ' ' + patient_lastname)
            f.write('\n')
            self.stderr.write('Patient Fetch Error: %s' % str(e))
            return
        try:
            episode = p.episodes.get(is_active=True)
            if not episode:
                raise Exception('No active episode found')
        except Exception as e:
            f.write(patient_firstname + ' ' + patient_lastname)
            f.write('\n')
            self.stderr.write('Episode Fetch Error: %s' % str(e))
            return

        user_roles = get_user_roles(row)
        for role in user_roles.keys():
            for user in user_roles[role]:
                if user:
                    userobj = get_user_obj(org, user, role)
                    if userobj:
                        profile = userobj.profile
                        try:
                            self.stdout.write('FETCHING ACCESS HERE')
                            access = UserEpisodeAccess.objects.filter(episode=episode, user=profile, organization=org)
                            if access.exists():
                                continue
                            else:
                                access = UserEpisodeAccess.objects.create(episode=episode, user=profile, organization=org, user_role=role)
                                self.stdout.write(self.style.SUCCESS('Entered Access Details to DB'))
                                send_pubnub_msg(p, profile.uuid, episode.uuid)
                        except Exception as e:
                            self.stderr.write('Access fetch or write error: %s' % str(e))
                    else:
                        g.write(str(user))
                        g.write('\n')
                        self.stderr.write('User %s Not Found in DB' % str(user))

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Opening and Parsing the CSV ...'))
            filepath = 'phi/management/data/uhh_user_patients_tagging.csv'
            data = _readfile(filepath)
        except Exception as e:
            self.stderr.write(str(e))
            raise e

        patient_errfile = open('patient_errs.csv', 'w')
        users_errfile = open('user_errs.csv', 'w')

        org_name = options['org'][0]
        print('')
        self.stdout.write('Organization Name is: %s' % str(org_name))
        print('')

        # 1. Insert or fetch the org
        orgs = Organization.objects.filter(name=org_name)
        if len(orgs) == 0:
            if options.get('add_org', 'False') == 'True':
                self.stdout.write("Organization doesn't exist. Inserting it ...")
                org = Organization(name=org_name, address=None, contact_no=None, type=constants.ORG_TYPE_HOME_HEALTH)
                org.save()
                self.stdout.write('Saved Organization')
            else:
                raise Exception('Matching organization not found ...')
        elif len(orgs) > 1:
            raise Exception('More than 1 matching org found. Exiting ...')
        else:
            org = orgs[0]

        shape = data.shape
        print('No of patients:', shape[0])

        for i in data.index[:]:
            row = data.loc[i]
            print('')
            self.process_row(org, row, patient_errfile, users_errfile)
            print('')

        patient_errfile.close()
        users_errfile.close()

        self.stdout.write(self.style.SUCCESS('Data insert completed.'))
