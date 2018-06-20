from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from phi.management.commands.utils import constants
from phi.models import Patient, Episode, OrganizationPatientsMapping
from user_auth.models import Organization, Address
from django.db import transaction
import datetime

# def add_error_file_header(timestamp, sheetname, header):
#     filename = settings.ERROR_UPLOAD_DIR + sheetname + '_' + timestamp + '_errors.csv'
#     header.append('"""Error Msg"""')
#     s = ','.join(header)
#     with open(filename, 'a') as f:
#         f.write(s)
#         f.write('\n')


def _readfile(filepath):
    try:
        data = pd.read_csv(filepath, keep_default_na=False)
    except Exception as e:
        raise e
    headers = list(data.columns.values)
    print('')
    print('Headers are:', headers)
    print('')
    return data


class Command(BaseCommand):
    help = 'Add users to the DB from the CSV'

    def add_arguments(self, parser):
        parser.add_argument('org', nargs='+', type=str)

    def process_row(self, org, row):
        first_name = row.get(constants.FIRSTNAME)
        last_name = row.get(constants.LASTNAME)
        primary_contact = row.get(constants.PHONE)
        if primary_contact:
            primary_contact = primary_contact.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')
        emergency_contact = row.get(constants.EMERGENCYCONTACTPHONE)
        gender = row.get(constants.GENDER)
        if gender:
            if gender.lower() == 'female':
                gender = 'F'
                title = 'Ms'
            elif gender.lower() == 'male':
                gender = 'M'
                title = 'Mr'
            else:
                gender = 'O'
        else:
            gender = None
        medical_record_no = row.get(constants.MEDICALRECORDNO)
        hic_no = row.get(constants.HICNO)

        # Address Details
        # apartment_no = row.get(constants.ADDRESS2)
        street_address = row.get(constants.ADDRESS)
        city = row.get(constants.CITY)
        state = row.get(constants.STATE)
        country = row.get(constants.COUNTRY, 'USA')
        zip_code = row.get(constants.ZIPCODE)

        # Episode Details
        try:
            soc_date = datetime.datetime.strptime(row.get(constants.SOCSTARTDATE, '%m/%d/%Y'))
        except Exception as e:
            soc_date = None
        try:
            end_date = datetime.datetime.strptime(row.get(constants.SOCENDDATE, '%m/%d/%Y'))
        except Exception as e:
            end_date = None
        try:
            dob = datetime.datetime.strptime(row.get(constants.DOB), '%m/%d/%Y')
        except Exception as e:
            dob = None

        try:
            with transaction.atomic():
                # Save address to db
                try:
                    address = Address(street_address=street_address, city=city,
                                      zip=zip_code, state=state, country=country)
                    address.save()
                except Exception as e:
                    self.stderr.write('Address Save failed for: %s %s. Error: %s' % (first_name, last_name, str(e)))
                    raise e

                try:
                    # Save patient to db
                    patient = Patient(first_name=first_name, last_name=last_name, dob=dob, title=title,
                                      primary_contact=primary_contact, emergency_contact=emergency_contact,
                                      address=address, gender=gender, medical_record_no=medical_record_no,
                                      hic_no=hic_no)
                    patient.save()
                except Exception as e:
                    self.stderr.write('Patient Save failed. Error: %s' % str(e))
                    raise e

                try:
                    # Todo: Not saving Case Manager, Pharmacy, Physicians currently
                    # Save episode to db
                    episode = Episode(patient=patient, soc_date=soc_date, end_date=end_date)
                    episode.save()
                except Exception as e:
                    self.stderr.write('Episode Save failed. Error: %s' % str(e))
                    raise e

                # Save OrganizationPatientMapping to db
                try:
                    mapping = OrganizationPatientsMapping(organization=org, patient=patient)
                    mapping.save()
                except Exception as e:
                    self.stderr.write('Organization-Patient Mapping failed. Error: %s' % str(e))
                    raise e
        except Exception as e:
            self.stderr.write('Could not write patient: %s %s' % (first_name, last_name))

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Opening and Parsing the CSV ...'))
            filepath = 'phi/management/data/patients.csv'
            data = _readfile(filepath)
        except Exception as e:
            self.stderr.write(str(e))
            raise e

        org_name = options['org'][0]
        print('')
        print('Organization Name is:', org_name)
        print('')

        # 1. Fetch the org
        orgs = Organization.objects.filter(name=org_name)
        if len(orgs) == 0:
            raise Exception('Matching organization not found ...')
        elif len(orgs) > 1:
            raise Exception('More than 1 matching org found. Exiting ...')
        else:
            org = orgs[0]

        shape = data.shape
        print('No of patients:', shape[0])
        for i in data.index[:]:
            row = data.loc[i]
            self.process_row(org, row)

        self.stdout.write(self.style.SUCCESS('Data insert completed.'))

