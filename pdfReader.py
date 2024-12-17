#!/usr/bin/env python3

import csv
import getopt
import os
import re
import sys

import pdfplumber

keywords = ["Lastschrift", "Ueberweisung", "Gutschrift", "Entgelt", "Gehalt/Rente"]


def convert_file(input_file):
    path, file_name = os.path.split(input_file)
    output_file = os.path.join(path, f"{os.path.splitext(file_name)[0]}.csv")

    with pdfplumber.open(input_file) as pdf, open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Date",
                "Amount (Credit)",
                "Amount (Debit)",
                "Category Name",
                "purpose",
            ]
        )

        for idx, page in enumerate(pdf.pages[:-1]):
            txt = page.extract_text().split("\n")
            for line in txt:
                date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", line)
                keyword_found = any(keyword in line for keyword in keywords)

                if date_match and keyword_found:
                    if date_match.start() != 0:
                        line = line[date_match.start() :]
                    date = date_match.group()

                    amount_match = re.search(r"-?\d+\.?\d*,\d{2}", line)
                    if amount_match:
                        amount = amount_match.group().replace(".", "").replace(",", ".")
                    else:
                        amount = "0.00"

                    line = (
                        line.replace(date, "")
                        .replace(amount_match.group() if amount_match else "", "")
                        .replace(",", ";")
                    )

                    category, purpose = get_category_purpose(line)

                    writer.writerow([date, amount, category, purpose])


def get_category_purpose(line):
    """
    Determines the category and purpose from a line based on keywords.
    """
    category = "undefined"
    purpose = "undefined"
    for key in keywords:
        if key in line:
            category = key
            purpose = line.replace(key, "").strip()
            break
    return category, purpose


if __name__ == "__main__":
    user_provided_path = os.getcwd()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:")
    except getopt.GetoptError:
        print("you need to pass an argument in the form: test.py -i <inputfile>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("test.py -i <inputfile>")
            sys.exit()
        elif opt == "-i":
            user_provided_path = arg
    print("Input file is: ", user_provided_path)

    if os.path.isdir(user_provided_path):
        for filename in os.listdir(user_provided_path):
            print(user_provided_path + "/" + filename)
            convert_file(user_provided_path + "/" + filename)
        print("folder converted sucessfully")
    elif os.path.isfile(user_provided_path):
        convert_file(user_provided_path)
        print("file converted succesfully")
    else:
        print(
            "Something went wrong. Check that the path you provide is valid and redirects either to a .pdf or "
            "a directory with only pdfs."
        )
    sys.exit()
