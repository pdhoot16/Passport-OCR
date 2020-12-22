import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc

import os
import re
import cv2
import json
import tkinter
import datetime
import pytesseract
import numpy as np
from tkinter import filedialog

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
states = ("Andhra Pradesh", "Arunachal Pradesh ", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
          "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
          "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
          "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
          "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli", "Daman and Diu", "Lakshadweep",
          "National Capital Territory of Delhi", "Puducherry")


# Method to extract date of issue and expiry
def find_dates(text):
    date = re.findall('\d{2}/\d{2}/\d{4}', text)
    if (len(date) == 3):
        date_of_birth = date[0]
        date_of_issue = date[1]
        date_of_expiry = date[2]
    elif (len(date) == 2):
        date_of_birth = "00/00/0000"
        date_of_issue = date[0]
        date_of_expiry = date[1]
    else:
        date_of_birth = "00/00/0000"
        date_of_issue = "00/00/0000"
        date_of_expiry = "00/00/0000"
    return date_of_birth, date_of_issue, date_of_expiry


# Method to extract MRZ code
def find_mrz_code(text):
    mrz_code = text.split("P<", 1)[1]
    mrz_code = mrz_code.replace(" ", "")
    return mrz_code


# Method to extract name
def find_name(text):
    mrz_code = find_mrz_code(text)
    last_name = mrz_code.split("<<", 1)[0]
    last_name = last_name[3:]
    given_name = mrz_code.split("<<", 2)[1]
    given_name = given_name.replace("<", " ")
    return given_name, last_name


# Method to extract Passport number
def find_passport_no(text):
    mrz_code = find_mrz_code(text)
    p_no = mrz_code.split("\n", 1)[1]
    return p_no[0:8]


def find_gender(text):
    if text.find(" M ") > 0:
        return "Male"
    elif text.find(" F ") > 0:
        return "Female"
    else:
        return "Unknown"


def find_place_of_birth(text):
    birth_place = ""
    li = text.splitlines(True)
    indx = text.find(",")
    for i in range(0, len(li)):
        line_text = li[i]
        if (line_text.find(",") > 0):
            for state in states:
                if (line_text.find(state.upper())) > 0:
                    birth_place = re.sub('[^A-Z]+', ' ', line_text)
    return birth_place


def file_no(text):
    lines = text.splitlines(True)
    file_no = lines[-2]
    file_no = re.sub('[^A-Za-z0-9]+', '', file_no)
    file_no = file_no[0:15]
    return file_no


def find_address(text):
    li = text.splitlines(True)
    address = ""
    for i in range(0, len(li)):
        line_text = li[i]
        if (line_text.find("PIN") > -1):
            address = li[i - 2] + li[i - 1] + li[i]
    return address


def names(text):
    li = text.splitlines(True)
    guardian_name = ""
    mother_name = ""
    spouse_name = ""

    for i in range(0, len(li)):
        line_text = li[i]
        if (line_text.find("Name of Father") > 0):
            guardian_name = next_line_text = li[i + 1]
            guardian_name = re.sub('[^A-Z]+', ' ', guardian_name)
        if (line_text.find("Name of Mother") > 0):
            mother_name = next_line_text = li[i + 1]
            mother_name = re.sub('[^A-Z]+', ' ', mother_name)
        if (line_text.find("Name of Spouse") > 0):
            spouse_name = next_line_text = li[i + 1]
            spouse_name = re.sub('[^A-Z]+', ' ', spouse_name)
    return guardian_name, mother_name, spouse_name


app = dash.Dash()
server = app.server
app.layout = html.Div([
    html.Label([
        html.Label("Select front page of passport:"),
        dcc.Upload([html.Button('Upload File')], id='front-upload'),
        html.Br(),
        html.Div([html.Label("Given Name: "),
                  html.Label(id="given-name")]),
        html.Div([html.Label("Surname: "),
                  html.Label(id="surname")]),
        html.Div([html.Label("Passport No: "),
                  html.Label(id="passport-no")]),
        html.Div([html.Label("Gender: "),
                  html.Label(id="gender")]),
        html.Div([html.Label("MRZ code: "),
                  html.Label(id="mrz-code")]),
        html.Div([html.Label("Date of Birth: "),
                  html.Label(id="dob")]),
        html.Div([html.Label("Date of Issue: "),
                  html.Label(id="doi")]),
        html.Div([html.Label("Date of Expiry: "),
                  html.Label(id="doe")]),
        html.Div([html.Label("Place of Birth: "),
                  html.Label(id="birth-place")])
    ]),
    html.Hr(),
    html.Label([
        html.Label("Select last page of passport:"),
        dcc.Upload(html.Button('Upload File'), id='back-upload'),
        html.Br(),
        html.Div([html.Label("Name of Father/Guardian : "),
                  html.Label(id="father-name")]),
        html.Div([html.Label("Name of Mother : "),
                  html.Label(id="mother-name")]),
        html.Div([html.Label("Name of Spouse : "),
                  html.Label(id="spouse-name")]),
        html.Div([html.Label("Address : "),
                  html.Label(id="address")]),
        html.Div([html.Label("File No : "),
                  html.Label(id="file-no")])
    ])
])


@app.callback(
    [dash.dependencies.Output('given-name', 'children'),
     dash.dependencies.Output('surname', 'children'),
     dash.dependencies.Output('dob', 'children'),
     dash.dependencies.Output('doi', 'children'),
     dash.dependencies.Output('doe', 'children'),
     dash.dependencies.Output('mrz-code', 'children'),
     dash.dependencies.Output('birth-place', 'children'),
     dash.dependencies.Output('gender', 'children'),
     dash.dependencies.Output('passport-no', 'children')],
    [dash.dependencies.Input('front-upload', 'filename')]
)
def frontpage_ocr(selected_value):
    custom_config = r'--oem 3 --psm 6'
    img = cv2.imread(selected_value)
    img_text = pytesseract.image_to_string(img, config=custom_config)
    dates = find_dates(img_text)
    dob = dates[0]
    doi = dates[1]
    doe = dates[2]
    mrz_code = find_mrz_code(img_text)
    given_name = find_name(img_text)[0]
    surname = find_name(img_text)[1]
    passport_no = find_passport_no(img_text)
    gender = find_gender(img_text)
    place_of_birth = find_place_of_birth(img_text)
    #     data_front = {'Given Name': given_name, 'Surname':surname ,'Passport No.':passport_no, 'Gender':gender,
    #                   'Place of Birth':place_of_birth,
    #                   'Date of Birth':dob, 'Date of Issue':doi, 'Date of Expiry':doe,
    #                   'MRZ code':mrz_code}
    #     json_front = json.dumps(data_front)
    return given_name, surname, dob, doi, doe, mrz_code, place_of_birth, gender, passport_no


@app.callback(
    [dash.dependencies.Output('father-name', 'children'),
     dash.dependencies.Output('mother-name', 'children'),
     dash.dependencies.Output('spouse-name', 'children'),
     dash.dependencies.Output('address', 'children'),
     dash.dependencies.Output('file-no', 'children')],
    [dash.dependencies.Input('back-upload', 'filename')]
)
def backpage_ocr(selected_value):
    custom_config = r'--oem 3 --psm 6'
    img = cv2.imread(selected_value)
    img_text = pytesseract.image_to_string(img, config=custom_config)
    names_list = names(img_text)
    father_name = names_list[0]
    mother_name = names_list[1]
    spouse_name = names_list[2]
    address = find_address(img_text)
    f_no = file_no(img_text)
    return father_name, mother_name, spouse_name, address, f_no


if __name__ == '__main__':
    app.run_server()