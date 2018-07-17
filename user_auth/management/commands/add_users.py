from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from user_auth.management.commands.utils import constants
from user_auth.models import Organization, UserProfile, User, Address, UserOrganizationAccess
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

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
    logger.info('Headers are: %s' % str(headers))
    print('')
    return data


class Command(BaseCommand):
    help = 'Add users to the DB from the CSV'

    def add_arguments(self, parser):
        parser.add_argument('org', nargs=1, type=str)
        parser.add_argument('--add-org', help='Force push the Org name',)

    def process_row(self, org, row):
        first_name = row.get(constants.FIRSTNAME)
        last_name = row.get(constants.LASTNAME)
        role = row.get(constants.SUFFIX)
        phone1 = row.get(constants.PHONE1)
        phone2 = row.get(constants.PHONE2)
        dob = row.get(constants.DOB)
        password = row.get(constants.PASSWORD)
        username = str(first_name).strip().lower() + '.' + str(last_name).strip().lower()
        email = str(first_name).strip().lower() + '.' + str(last_name).strip().lower() + '@freudenthalhh.com'
        # Address Details
        street_address = row.get(constants.ADDRESS1)
        apartment_no = row.get(constants.ADDRESS2)
        city = row.get(constants.CITY)
        state = row.get(constants.STATE)
        country = row.get(constants.COUNTRY, 'USA')
        zip_code = row.get(constants.ZIPCODE)

        if phone1:
            phone1 = phone1.replace(')', '').replace('(', '').replace('-', '').replace(' ', '')

        try:
            with transaction.atomic():
                # Save user to db
                user = User.objects.create_user(first_name=first_name, last_name=last_name,
                                                username=username, password=password, email=email)
                user.save()

                # Save address to db
                try:
                    address = Address(apartment_no=apartment_no, street_address=street_address, city=city,
                                      zip=zip_code, state=state, country=country)
                    address.save()
                except Exception as e:
                    self.stderr.write('Address Save failed for: %s %s. Error: %s' % (first_name, last_name, str(e)))

                # Save user profile to db
                profile = UserProfile(user=user, title='', contact_no=phone1, address=address)
                profile.save()

                # Add entry to UserOrganizationAccess: For that org, add all users, and their 'roles'
                access = UserOrganizationAccess(user=profile, organization=org, user_role=role)
                access.save()
        except Exception as e:
            self.stderr.write('Could not write user: %s %s' % (first_name, last_name))

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Opening and Parsing the CSV ...'))
            filepath = 'user_auth/management/data/employees.csv'
            data = _readfile(filepath)
        except Exception as e:
            self.stderr.write(str(e))
            raise e

        org_name = options['org'][0]
        print('')
        logger.info('Organization Name is: %s' % str(org_name))
        print('')

        # 1. Insert or fetch the org
        orgs = Organization.objects.filter(name=org_name)
        if len(orgs) == 0:
            if options.get('add_org', 'False') == 'True':
                logger.info("Organization doesn't exist. Inserting it ...")
                org = Organization(name=org_name, address=None, contact_no=None, type=constants.ORG_TYPE_HOME_HEALTH)
                org.save()
                logger.info('Saved Organization')
            else:
                raise Exception('Matching organization not found ...')
        elif len(orgs) > 1:
            raise Exception('More than 1 matching org found. Exiting ...')
        else:
            org = orgs[0]

        for i in data.index[:]:
            row = data.loc[i]
            self.process_row(org, row)

        self.stdout.write(self.style.SUCCESS('Data insert completed.'))

