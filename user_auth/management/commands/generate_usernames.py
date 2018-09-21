from django.core.management.base import BaseCommand
import pandas as pd
from user_auth.management.commands.utils import constants
import logging
import random

logger = logging.getLogger(__name__)

BASE_PATH = 'user_auth/management/data/'


def generate_username(firstname, lastname):
    first_name = firstname.apply(lambda x: x.lower().replace(')', '').replace('(', '').replace('-', '').replace(' ', ''))
    last_name = lastname.apply(lambda x: x.lower().replace(')', '').replace('(', '').replace('-', '').replace(' ', ''))
    suffix = '@uhh.health'
    username = first_name + '.' + last_name + suffix
    return username


def generate_random_password(count):
    passwds = []
    for i in range(count):
        digits = [str(random.randint(0,9)) for _ in range(5)]
        passwd = ''.join(digits)
        passwds.append(passwd)
    return pd.Series(passwds, index=None)


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
    help = 'Generate credentials for users'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str, help='Filename to make changes to')

    def handle(self, *args, **options):
        try:
            filename = options['filename'][0]
            self.stdout.write('FileName is: %s' % str(filename))
            self.stdout.write(self.style.SUCCESS('Opening and Parsing the CSV ...'))
            filepath = BASE_PATH + filename + '.csv'
            data = _readfile(filepath)
        except Exception as e:
            self.stderr.write(str(e))
            raise e

        self.stdout.write('Shape of data: %s' % str(data.shape))

        columns = data.columns
        print(columns)

        if constants.EMAIL in columns:
            data[constants.USERNAME] = data[constants.EMAIL]
        else:
            # Try to generate usernames
            data[constants.FIRSTNAME] = data[constants.FIRSTNAME].apply(lambda x: x.strip())
            data[constants.LASTNAME] = data[constants.LASTNAME].apply(lambda x: x.strip())
            data[constants.USERNAME] = generate_username(data[constants.FIRSTNAME], data[constants.LASTNAME])
        data[constants.PASSWORD] = generate_random_password(data.shape[0])

        self.stdout.write('Saving data to new file ...')
        data.to_csv(BASE_PATH + filename + '2.csv')

        self.stdout.write(self.style.SUCCESS('Added usernames for all rows.'))
