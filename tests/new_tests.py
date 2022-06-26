import json

from tests.unit_test import request, check_nodes

with open('test_data/test_group.json', mode='r', encoding='utf-8') as file:
    tests = json.load(file)
    test_number = 0
    for test in tests['tests']:
        test_number += 1
        if test['url'].startswith('/imports'):
            status, response = request(
                test['url'], method=test['method'], data=test['data'],
                json_response=True)

            assert status == test['result']['status'], \
                f'Expected HTTP status code 200, got {status}'

            assert response == test['result']['json'], \
                f"Invalid request body: {response}"

        elif test['url'].startswith('/nodes'):
            status, response = request(
                test['url'], method=test['method'], json_response=True)

            assert status == test['result']['status'], \
                f"Expected HTTP status code {test['result']['status']}, got {status}"

            if status == 200:
                check_nodes(test['result']['json'], response)

        elif test['url'].startswith('/delete'):
            status, _ = request(test['url'], method=test['method'])

            assert status == test['result']['status'], \
                f"Expected HTTP status code {test['result']['status']}, got {status}"
        else:
            print(f'Test {test_number} missing!')

        print(f'Test {test_number} passed.')

print('Test group passed')
