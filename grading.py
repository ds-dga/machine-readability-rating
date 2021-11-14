def calculate_grade(point):
    if point == 100:
        return "a+"
    if point > 90:
        return "a"
    if point > 85:
        return "a-"
    if point > 80:
        return "b+"
    if point >= 70:
        return "b"
    return "f"
