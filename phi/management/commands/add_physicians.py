from django.core.management.base import BaseCommand
import pandas as pd
from phi.management.commands.utils import constants
from phi.models import Patient, Episode, UserEpisodeAccess, Physician
from django.db import transaction
from django.conf import settings
import datetime


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

    def publish_update_message(self, user_uuid, patient_uuid):
        self.stdout.write('Publishing update message for ' + str(user_uuid) + ' - ' + str(patient_uuid))
        settings.PUBNUB.publish().channel(str(user_uuid) + '_assignedPatients').message({
            'actionType': 'UPDATE',
            'patientID': str(patient_uuid),
        }).async(my_publish_callback)

    def process_row(self, row):
        first_name = row.get(constants.FIRSTNAME)
        last_name = row.get(constants.LASTNAME)
        primary_contact = row.get(constants.PHONE)
        if primary_contact:
            primary_contact = primary_contact.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')
        npi = str(row.get(constants.NPI))
        physician_contact = row.get(constants.PHYSICIANCONTACT)
        if physician_contact:
            physician_contact = physician_contact.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')

        try:
            with transaction.atomic():
                try:
                    patient = Patient.objects.get(first_name=first_name, last_name=last_name,
                                                  primary_contact=primary_contact)
                    try:
                        episode = patient.episodes.get(is_active=True)
                        try:
                            physician = Physician.objects.get(npi=npi)
                            if physician.phone1 != physician_contact:
                                physician.phone2 = physician_contact
                            physician.save()
                            episode.primary_physician = physician
                            episode.save()
                            self.stdout.write('Saving physician for : %s %s %s' % (first_name, last_name, npi))
                            user_episode_access_list = UserEpisodeAccess.objects.filter(episode=episode)
                            if user_episode_access_list.count() > 0:
                                users_linked_to_patient = [user_episode_access.user.uuid for user_episode_access in
                                                           user_episode_access_list]
                                for user_uuid in users_linked_to_patient:
                                    self.stdout.write('USER ID: %s' % str(user_uuid))
                                    self.publish_update_message(user_uuid, patient.uuid)
                        except Physician.DoesNotExist as e:
                            self.stderr.write('Physician not found for npi : %s' % str(npi))
                            raise e
                    except Episode.DoesNotExist as e:
                        self.stderr.write('Active episode not found for patient: %s %s %s' % (first_name, last_name, primary_contact))
                        raise e
                except Exception as e:
                    self.stderr.write('Patient Update failed. Error: %s' % str(e))
                    raise e
        except Exception as e:
            self.stderr.write('Could not UPDATE patient: %s %s' % (first_name, last_name))

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Opening and Parsing the CSV ...'))
            filepath = 'phi/management/data/patients.csv'
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

