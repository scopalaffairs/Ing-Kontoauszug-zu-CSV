#!/usr/bin/env python3

import csv
import getopt
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber
from colorama import Fore, Style

keywords = [
    "Lastschrift",
    "Ueberweisung",
    "Gutschrift",
    "Entgelt",
    "Gehalt/Rente",
    "Dauerauftrag/Terminueberw.",
]


def ensure_output_dir(input_dir):
    """
    Ensure the output directory exists at the same level as the input directory.
    Returns the path to the output directory.
    """
    input_dir = Path(input_dir).resolve()
    output_dir = input_dir.parent / "csv"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def convert_date_format(date):
    """
    Converts date from DD.MM.YYYY to YYYY-MM-DD format.
    """
    try:
        return datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return date


def normalize_text(text):
    """
    Normalize text by stripping spaces and converting to lowercase.
    """
    return text.strip().lower()


missing_purposes_global = set()


def compare_purposes(purposes_from_docs):
    """
    Compare extracted purposes with the predefined keyword list.
    """
    global missing_purposes_global
    normalized_keywords = {normalize_text(k) for k in keywords}
    normalized_purposes = {normalize_text(p) for p in purposes_from_docs}

    missing_purposes = normalized_purposes - normalized_keywords
    extra_purposes = normalized_keywords - normalized_purposes

    missing_purposes_global.update(missing_purposes)

    if missing_purposes:
        print(
            f"{Fore.RED}Missing purposes in keyword list:{Style.RESET_ALL} {missing_purposes}"
        )
    else:
        print(
            f"{Fore.GREEN}No missing purposes. Keywords cover all extracted purposes.{Style.RESET_ALL}"
        )

    if extra_purposes:
        print(
            f"{Fore.YELLOW}Extra purposes in keyword list:{Style.RESET_ALL} {extra_purposes}"
        )
    else:
        print(f"{Fore.GREEN}No extra purposes in the keyword list.{Style.RESET_ALL}")


def convert_file(input_file, output_dir):
    """
    Convert a single PDF file to CSV format and save it to the specified output directory.
    """
    file_name = Path(input_file).stem
    output_file = output_dir / f"{file_name}.csv"

    purposes_from_docs = set()

    with pdfplumber.open(input_file) as pdf, open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Date", "Credit Amount", "Debit Amount", "Category", "Purpose"]
        )

        for page in pdf.pages:
            text_lines = page.extract_text().split("\n") if page.extract_text() else []
            for line in text_lines:
                date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", line)
                if date_match and any(keyword in line for keyword in keywords):
                    date = convert_date_format(date_match.group())
                    line = line[date_match.end() :].strip()

                    amount_match = re.search(r"-?\d+\.?\d*,\d{2}", line)
                    if amount_match:
                        amount = amount_match.group().replace(".", "").replace(",", ".")
                        amount = float(amount)
                        credit_amount = amount if amount > 0 else 0.0
                        debit_amount = abs(amount) if amount < 0 else 0.0
                        line = line.replace(amount_match.group(), "").strip()
                    else:
                        credit_amount, debit_amount = 0.0, 0.0

                    category, purpose = get_category_purpose(line)
                    purposes_from_docs.add(category)  # Collect extracted purposes
                    writer.writerow(
                        [date, credit_amount, debit_amount, category, purpose]
                    )

    compare_purposes(purposes_from_docs)  # Compare extracted purposes with keywords


def get_category_purpose(line):
    """
    Determines the category and purpose from a line based on keywords.
    """
    for keyword in keywords:
        if keyword in line:
            category = keyword
            purpose = line.replace(keyword, "").strip()
            return category, purpose
    return "undefined", line.strip()


def convert_files_in_dir(input_dir):
    """
    Convert all PDF files in a directory to CSV format.
    """
    input_dir = Path(input_dir).resolve()
    output_dir = ensure_output_dir(input_dir)

    for file in input_dir.iterdir():
        if file.is_file() and file.suffix.lower() == ".pdf":
            print(f"Processing file: {file}")
            convert_file(file, output_dir)

    print(
        f"All files in {input_dir} converted successfully. CSVs saved in {output_dir}"
    )


def summarize_missing_purposes():
    """
    Summarize any missing purposes after all files are processed.
    """
    global missing_purposes_global
    if missing_purposes_global:
        print(
            f"\n{Fore.RED}Summary of missing purposes across all documents:{Style.RESET_ALL}"
        )
        for purpose in missing_purposes_global:
            print(f"- {purpose}")
    else:
        print(
            f"\n{Fore.GREEN}No missing purposes across all documents. All purposes are covered by keywords.{Style.RESET_ALL}"
        )


def main():
    """
    Main function to parse arguments and trigger conversion.
    """
    input_path = os.getcwd()
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hi:")
    except getopt.GetoptError:
        print("Usage: script.py -i <input_path>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print("Usage: script.py -i <input_path>")
            sys.exit()
        elif opt == "-i":
            input_path = arg

    input_path = Path(input_path).resolve()

    if input_path.is_dir():
        convert_files_in_dir(input_path)
        summarize_missing_purposes()
    elif input_path.is_file() and input_path.suffix.lower() == ".pdf":
        output_dir = ensure_output_dir(input_path.parent)
        convert_file(input_path, output_dir)
        summarize_missing_purposes()
        print(f"File {input_path} converted successfully. CSV saved in {output_dir}")
    else:
        print(
            "Error: Invalid input. Provide a valid PDF file or a directory containing PDF files."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
