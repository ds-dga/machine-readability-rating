import openpyxl

""" XLS, XLSX grader
1. check if it's excel file.
2. check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
3. data consistency
"""