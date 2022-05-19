# Machine readability

This is a grader for all files. Rules are as follows:

* Valid JSON, XML, yaml, toml yields A+, no question asked.
* CSV grade can be from F, B, B+, A, A+

## CSV rules

* CSV with single header row
    A+

* csv without header, but provides data description
    A

* csv with non-unicode encoding
    B+

* csv with inconsistency data
    B

### Bad CSV
* csv with multiple header row
* without header & no data description
* unstructure



# status_code

    590 - big file
    591 - internal URL
    595 - requests.exceptions.ReadTimeou
    599 - unknown