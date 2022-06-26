# encoding=utf8

import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASEURL = "https://funded-1989.usr.yandex-academy.ru"

ROOT_ID = "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"

IMPORT_BATCHES = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Смартфоны",
                "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "jPhone 13",
                "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 79999
            },
            {
                "type": "OFFER",
                "name": "Xomiа Readme 10",
                "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 59999
            }
        ],
        "updateDate": "2022-02-02T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Телевизоры",
                "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "Samson 70\" LED UHD Smart",
                "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 32999
            },
            {
                "type": "OFFER",
                "name": "Phyllis 50\" LED UHD Smarter",
                "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 49999
            }
        ],
        "updateDate": "2022-02-03T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            }
        ],
        "updateDate": "2022-02-03T15:00:00.000Z"
    }
]

EXPECTED_TREE = {
    "type": "CATEGORY",
    "name": "Товары",
    "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
    "price": 58599,
    "parentId": None,
    "date": "2022-02-03T15:00:00.000Z",
    "children": [
        {
            "type": "CATEGORY",
            "name": "Телевизоры",
            "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "price": 50999,
            "date": "2022-02-03T15:00:00.000Z",
            "children": [
                {
                    "type": "OFFER",
                    "name": "Samson 70\" LED UHD Smart",
                    "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 32999,
                    "date": "2022-02-03T12:00:00.000Z",
                    "children": None,
                },
                {
                    "type": "OFFER",
                    "name": "Phyllis 50\" LED UHD Smarter",
                    "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 49999,
                    "date": "2022-02-03T12:00:00.000Z",
                    "children": None
                },
                {
                    "type": "OFFER",
                    "name": "Goldstar 65\" LED UHD LOL Very Smart",
                    "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 69999,
                    "date": "2022-02-03T15:00:00.000Z",
                    "children": None
                }
            ]
        },
        {
            "type": "CATEGORY",
            "name": "Смартфоны",
            "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "price": 69999,
            "date": "2022-02-02T12:00:00.000Z",
            "children": [
                {
                    "type": "OFFER",
                    "name": "jPhone 13",
                    "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "price": 79999,
                    "date": "2022-02-02T12:00:00.000Z",
                    "children": None
                },
                {
                    "type": "OFFER",
                    "name": "Xomiа Readme 10",
                    "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "price": 59999,
                    "date": "2022-02-02T12:00:00.000Z",
                    "children": None
                }
            ]
        },
    ]
}


def request(path, method="GET", data=None, json_response=False):
    try:
        params = {
            "url": f"{API_BASEURL}{path}",
            "method": method,
            "headers": {},
        }

        if data:
            params["data"] = json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            params["headers"]["Content-Length"] = len(params["data"])
            params["headers"]["Content-Type"] = "application/json"

        req = urllib.request.Request(**params)

        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode("utf-8")

            if json_response:
                res_data = json.loads(res_data)
            return (res.getcode(), res_data)
    except urllib.error.HTTPError as e:
        return (e.getcode(), None)


def deep_sort_children(node):
    if node.get("children"):
        node["children"].sort(key=lambda x: x["id"])

        for child in node["children"]:
            deep_sort_children(child)


def print_diff(expected, response):
    with open("expected.json", "w") as f:
        json.dump(expected, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with open("response.json", "w") as f:
        json.dump(response, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    subprocess.run(["git", "--no-pager", "diff", "--no-index",
                    "expected.json", "response.json"])


def check_nodes(expected, response):
    deep_sort_children(response)
    deep_sort_children(expected)
    if response != expected:
        print_diff(expected, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)


def test_import():
    for index, batch in enumerate(IMPORT_BATCHES):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    print("Test import passed.")


def test_nodes():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 200, f"Expected HTTP status code 200, got {status}"

    check_nodes(EXPECTED_TREE, response)

    print("Test nodes passed.")


def test_sales():
    params = urllib.parse.urlencode({
        "date": "2022-02-04T00:00:00.000Z"
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test sales passed.")


def test_stats():
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T00:00:00.000Z",
        "dateEnd": "2022-02-03T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)

    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test stats passed.")


def test_delete():
    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete passed.")


def test_cascade_delete():
    for index, batch in enumerate(IMPORT_BATCHES):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    print(f"Delete root {ROOT_ID}")

    batches = []

    for b in IMPORT_BATCHES:
        batches.extend(b['items'])

    for batch in batches:
        status, response = request(f"/nodes/{batch['id']}", json_response=True)
        assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete cascade passed.")


def test_invalid_uuid():
    status, _ = request(f"/nodes/{0}", json_response=True)
    assert status == 400, f"Expected HTTP status code 400, got {status}"

    status, _ = request(f"/delete/{'asdfasdf-saf-1'}", method="DELETE")
    assert status == 400, f"Expected HTTP status code 400, got {status}"

    print("Test invalid uuid passed. ")


def test_cascade_update():
    root_id = "3fa85f64-5717-4562-b3fc-2c963f66a111"

    batch = {
        "items": [
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a222",
                "name": "Кат.2. Подкат. кат.1",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a111",
                "price": None,
                "type": "CATEGORY"
            },
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a333",
                "name": "Кат.3. Подкат. кат.2",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a222",
                "price": None,
                "type": "CATEGORY"
            },
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a444",
                "name": "Товар кат.1",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a111",
                "price": 1_000,
                "type": "OFFER"
            },
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a555",
                "name": "Товар кат.2",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a222",
                "price": 2_000,
                "type": "OFFER"
            },
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a666",
                "name": "Товар кат.3",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a333",
                "price": 3_000,
                "type": "OFFER"
            },
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a111",
                "name": "Кат. 1",
                "parentId": None,
                "price": None,
                "type": "CATEGORY"
            }
        ],
        "updateDate": "2020-02-20T20:20:20.000Z"
    }

    update_batch = {
        "items": [
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a222",
                "name": "Кат.2. Подкат. кат.1 (обновленная)",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a111",
                "price": None,
                "type": "CATEGORY"
            }
        ],
        "updateDate": "2077-02-20T20:20:20.000Z"
    }

    expected_update_batch = {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66a222",
        "name": "Кат.2. Подкат. кат.1 (обновленная)",
        "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a111",
        "price": 2_500,
        "type": "CATEGORY",
        "date": "2077-02-20T20:20:20.000Z",
        "children": [
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a555",
                "name": "Товар кат.2",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a222",
                "price": 2_000,
                "date": "2020-02-20T20:20:20.000Z",
                "type": "OFFER",
                "children": None
            },
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a333",
                "name": "Кат.3. Подкат. кат.2",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a222",
                "price": 3_000,
                "type": "CATEGORY",
                "date": "2020-02-20T20:20:20.000Z",
                "children": [
                    {
                        "id": "3fa85f64-5717-4562-b3fc-2c963f66a666",
                        "name": "Товар кат.3",
                        "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a333",
                        "price": 3_000,
                        "date": "2020-02-20T20:20:20.000Z",
                        "type": "OFFER",
                        "children": None
                    }
                ]
            }
        ]
    }

    expected_root_batch = {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66a111",
        "name": "Кат. 1",
        "parentId": None,
        "price": 2_000,
        "type": "CATEGORY",
        "date": "2077-02-20T20:20:20.000Z",
        "children": [
            expected_update_batch,
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a444",
                "name": "Товар кат.1",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a111",
                "price": 1_000,
                "type": "OFFER",
                "date": "2020-02-20T20:20:20.000Z",
                "children": None
            }
        ]
    }

    status, _ = request("/imports", method="POST", data=batch)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request("/imports", method="POST", data=update_batch)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, response = request(f"/nodes/{update_batch['items'][0]['id']}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    check_nodes(expected_update_batch, response)

    status, response = request(f"/nodes/{root_id}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    check_nodes(expected_root_batch, response)

    status, _ = request(f"/delete/{root_id}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    print("Test cascade update date passed.")


def test_json_groups():
    with open('json_groups/test_group.json', mode='r', encoding='utf-8') as file:
        tests = json.load(file)
        test_number = 0
        for test in tests['tests']:
            test_number += 1
            if test['url'].startswith('/imports'):
                status, response = request(
                    test['url'], method=test['method'].upper(), data=test['data'],
                    json_response=True)

                assert status == test['result']['status'], \
                    f'Expected HTTP status code 200, got {status}'

                assert response == test['result']['json'], \
                    f"Invalid request body: {response}"

            elif test['url'].startswith('/nodes'):
                status, response = request(
                    test['url'], method=test['method'].upper(), json_response=True)

                assert status == test['result']['status'], \
                    f"Expected HTTP status code {test['result']['status']}, got {status}"

                if status == 200:
                    check_nodes(test['result']['json'], response)

            elif test['url'].startswith('/delete'):
                status, _ = request(test['url'], method=test['method'].upper())

                assert status == test['result']['status'], \
                    f"Expected HTTP status code {test['result']['status']}, got {status}"
            else:
                print(f'Test {test_number} missing!')

            print(f'Test {test_number} passed.')

    print('Test group passed')


def test_all():
    """ Call all 'test_' functions. """

    """ Base test. """
    test_import()
    test_nodes()
    test_sales()
    test_stats()
    test_delete()

    """ Additional test. """
    test_cascade_delete()
    test_invalid_uuid()
    test_cascade_update()
    test_json_groups()


def main():
    global API_BASEURL
    test_name = None

    for arg in sys.argv[1:]:
        if re.match(r"^https?://", arg):
            API_BASEURL = arg
        elif test_name is None:
            test_name = arg

    if API_BASEURL.endswith('/'):
        API_BASEURL = API_BASEURL[:-1]

    if test_name is None:
        test_all()
    else:
        test_func = globals().get(f"test_{test_name}")
        if not test_func:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
        test_func()


if __name__ == "__main__":
    main()
