from db import Database
from grading import calculate_grade
from main import handle_url
from offsite import fetch_api

BASE_URL = "https://data.go.th"

db = Database()


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
    cursor = db.get_cursor()
    q = f"""SELECT grade, inspected
    FROM resource
    WHERE id = '{resourceID}'
    """
    cursor.execute(q)
    one = cursor.fetchone()
    return one


def resource_grader(item):
    points, encoding, note = handle_url(item["url"], item["format"])
    # print(item["url"], item["format"], flush=True)
    curr_grade, inspected = get_resource_grade(item["id"])
    print(f"   >>> inspected_on: {inspected}")
    grade = calculate_grade(points)
    if grade != curr_grade:
        db.resource_grade_update(item["id"], grade)
        # below this doesn't do anything but printing output
        grade_delta = f"{curr_grade} --> {grade}"
    else:
        grade_delta = f"{grade} -- same old"
    print(
        f"""== {item['id']} ================\n"""
        f"""1. {item['description']}\n"""
        f"""1. grade:               {grade_delta}\n"""
        f"""2. filetype:            {item['format']}\n"""
        f"""3. encoding:            {encoding}\n"""
        f"""4. Machine readable:    {points if points else '0'} % {note}""",
        flush=True,
    )
