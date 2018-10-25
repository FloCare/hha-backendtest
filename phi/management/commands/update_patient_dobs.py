from django.core.management.base import BaseCommand
import pandas as pd
# from phi.management.commands.utils import constants
from phi.models import Patient, Episode, UserEpisodeAccess
from django.db import transaction
from django.conf import settings
from datetime import datetime


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


def my_publish_callback(envelope, status):
    if not status.is_error():
        print( 'Message successfully published to specified channel.')
    else:
        print(' NOT Message successfully published to specified channel.')
        pass


class Command(BaseCommand):
    help = 'Update users data in the DB from the CSV'

    def publish_update_message(self, user_id, patient_id):
        self.stdout.write('Publishing update message for ' + str(user_id) + ' - ' +  str(patient_id))
        settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
            'actionType': 'UPDATE',
            'patientID': patient_id,
        }).async(my_publish_callback)

    def process_row(self, row):
        firstName = row.get('FirstName')
        lastName = row.get('LastName')
        dob = row.get('DOB')
        dob = datetime.strptime(dob, '%m/%d/%Y')

        try:
            with transaction.atomic():
                patient = Patient.objects.filter(first_name=firstName).get(last_name=lastName)
                print('Updating:', patient.dob, ' to ', dob, 'for', firstName, lastName)
                patient.dob = dob
                patient.save()
                episodes = Episode.objects.filter(patient_id=patient.uuid, is_active=True)
                if episodes.count() > 0:
                    print('episodes > 0')
                    all_episode_ids = [episode.uuid for episode in episodes]
                    user_episode_access_list = UserEpisodeAccess.objects.filter(episode_id__in=all_episode_ids)
                    if user_episode_access_list.count() > 0:
                        print('count > 0')
                        users_linked_to_patient = [user_episode_access.user.uuid for user_episode_access in user_episode_access_list]
                        for user_id in users_linked_to_patient:
                            self.publish_update_message(user_id, patient.uuid)
        except Exception as e:
            print('Error:', str(e))
            print('Not Found:', firstName, lastName)

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Opening and Parsing the CSV ...'))
            filepath = 'phi/management/data/data.csv'
            data = _readfile(filepath)
        except Exception as e:
            self.stderr.write(str(e))
            raise e
        shape = data.shape
        print('No of patients:', shape[0])
        for i in data.index[:]:
            row = data.loc[i]
            self.process_row(row)

        self.stdout.write(self.style.SUCCESS('Data insert completed.'))
