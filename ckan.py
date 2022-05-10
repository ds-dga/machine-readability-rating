import arrow
from db import Database
from grading import calculate_grade
from main import handle_url
from offsite import fetch_api

BASE_URL = "https://data.go.th"
db = None


def get_package_list():
    url = f"{BASE_URL}/api/3/action/package_list"
    resp = fetch_api(url)
    if not resp:
        return []
    if not resp["success"]:
        return []
    return resp["result"]


def get_package_detail(id):
    url = f"{BASE_URL}/api/3/action/package_show?id={id}"
    resp = fetch_api(url)
    if not resp:
        return []
    if not resp["success"]:
        return []
    return resp["result"]


def get_resource_grade(resourceID):
    global db
    if not db:
        db = Database()
    cursor = db.get_cursor()
    q = f"""SELECT grade, inspected
    FROM resource
    WHERE id = '{resourceID}'
    """
    cursor.execute(q)
    one = cursor.fetchone()
    return one


def resource_grader(item):
    global db
    if not db:
        db = Database()
    curr_grade, inspected = get_resource_grade(item["id"])
    now = arrow.get()
    # force to re-evaluate 'F' anyway
    if curr_grade != "f" and inspected and (now - arrow.get(inspected)).days < 7:
        print("    >>> SKIP too soon")
        return [
            item["package_id"],
            item["id"],
            now.isoformat(),
            item["url"],
            item["size"],
            "-1",
            curr_grade,
            curr_grade,
            f"encd:-|fs:-|too soon skip",
        ]

    points, encoding, note, file_size = handle_url(item["url"], item["format"])
    # print(item["url"], item["format"], flush=True)
    grade = "f"
    if note not in (404, 590, 599):
        grade = calculate_grade(points)

    db.resource_grade_update(item["id"], grade)
    # below this doesn't do anything but printing output
    if grade != curr_grade:
        grade_delta = f"{curr_grade} --> {grade}"
    else:
        grade_delta = f"{grade} -- same old"

    print(
        f"""== {item['id']} ================\n"""
        f"""0. {item['description']}\n"""
        f"""1. grade:               {grade_delta}\n"""
        f"""2. filetype:            {item['format']}\n"""
        f"""3. encoding:            {encoding}\n"""
        f"""4. Machine readable:    {points if points else '0'} % {note}\n"""
        f"""=================>>>""",
        flush=True,
    )

    return [
        item["package_id"],
        item["id"],
        now.isoformat(),
        item["url"],
        item["size"],
        points,
        grade,
        curr_grade,
        f"encd:{encoding}|fs:{file_size}|{note}",
    ]
