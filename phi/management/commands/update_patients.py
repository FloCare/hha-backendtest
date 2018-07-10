from django.core.management.base import BaseCommand
import pandas as pd
from phi.management.commands.utils import constants
from phi.models import Patient, Episode, UserEpisodeAccess
from django.db import transaction
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


class Command(BaseCommand):
    help = 'Update users data in the DB from the CSV'

    def process_row(self, row):
        first_name = row.get(constants.FIRSTNAME)
        last_name = row.get(constants.LASTNAME)
        primary_contact = row.get(constants.PHONE)
        if primary_contact:
            primary_contact = primary_contact.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')
        emergency_contact_phone = row.get(constants.EMERGENCYCONTACTPHONE)
        if emergency_contact_phone:
            emergency_contact_phone = emergency_contact_phone.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')
        emergency_contact_name = row.get(constants.EMERGENCYCONTACTNAME)
        emergency_contact_relation = row.get(constants.EMERGENCYCONTACTRELATION)

        try:
            dob = datetime.datetime.strptime(row.get(constants.DOB), '%m/%d/%Y')
        except Exception as e:
            dob = None

        try:
            with transaction.atomic():
                try:
                    patient = Patient.objects.get(first_name=first_name, last_name=last_name,
                                                  primary_contact=primary_contact)
                    if dob is not None:
                        patient.dob = dob
                    if emergency_contact_phone is not None:
                        patient.emergency_contact_number = emergency_contact_phone
                    if emergency_contact_relation is not None:
                        patient.emergency_contact_relation = emergency_contact_relation
                    if emergency_contact_name is not None:
                        patient.emergency_contact_name = emergency_contact_name
                    patient.save()

                    episodes = Episode.objects.filter(patient_id=patient.id, is_active=True)
                    if episodes.count() > 0:
                        all_episode_ids = [episode.id for episode in episodes]
                        user_episode_access_list = UserEpisodeAccess.objects.filter(episode_id__in=all_episode_ids)
                        if user_episode_access_list.count() > 0:
                            users_linked_to_patient = [user_episode_access.user.id for user_episode_access in
                                                       user_episode_access_list]
                #             USE user ids linked to patient
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

