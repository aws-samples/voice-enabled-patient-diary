
from src.data_access.user_profile import lookup_user_by_phone, lookup_user_by_id, UserProfile
from src.data_access.data_config import PROFILE_TABLE
import pytest
import boto3

table_name = PROFILE_TABLE

test_user = UserProfile(uid='123abc', phone="+1234567890", first_name='bob', zip_code='UTC', timezone='UTC')


@pytest.fixture()
def local_ddb(request):
    local_ddb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
    print('setting up tables in local ddb')
    local_ddb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'Patient_ID',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'Patient_ID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Phone_Num',
                'AttributeType': 'S'
            },
        ],
        BillingMode='PAY_PER_REQUEST',
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'Patient_by_Phone',
                'KeySchema': [
                    {
                        'AttributeName': 'Phone_Num',
                        'KeyType': 'HASH'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ],
    )
    local_ddb.Table(table_name).put_item(
        Item={
            'Patient_ID': test_user.uid,
            'First_Name': test_user.first_name,
            'Phone_Num': test_user.phone,
            'Zip_Code': test_user.zip_code,
            'Time_Zone': test_user.timezone
        })

    print(f'loaded test data in local ddb table: {table_name}')
    yield local_ddb
    local_ddb.Table(table_name).delete()


def test_lookup(local_ddb):
    res = lookup_user_by_phone(test_user.phone, ddb_client=local_ddb)
    assert res == test_user
    non_exist_number = '123456345'
    res = lookup_user_by_phone(non_exist_number, ddb_client=local_ddb)
    assert res is None

    res = lookup_user_by_id(test_user.uid, ddb_client=local_ddb)
    assert res == test_user
    non_exist_id = '123456345'
    res = lookup_user_by_phone(non_exist_id, ddb_client=local_ddb)
    assert res is None
