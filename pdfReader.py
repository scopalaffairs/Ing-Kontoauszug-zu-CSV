import pdfplumber
import re
import csv
import os
import sys
import getopt

keywords = ['Lastschrift', 'Ueberweisung', 'Gutschrift', 'Entgelt', 'Gehalt/Rente']


def convert_file(input_file):
    path, file_name = os.path.split(input_file)
    output_file = path + '/' + file_name.split('.')[0] + '.csv'
    with pdfplumber.open(input_file) as pdf:
        file = open(output_file, 'w')
        writer = csv.writer(file)
        writer.writerow(['date', 'amount', 'category', 'purpose'])

        for idx, page in enumerate(pdf.pages):
            if idx == len(pdf.pages) - 1:
                continue
            txt = page.extract_text().split('\n')
            for line in txt:
                reg_erg = re.search('\d{2}(\.){1}\d{2}(\.){1}\d{4}', line)
                if bool(reg_erg) and bool([ele for ele in keywords if (ele in line)]):
                    if reg_erg.start() != 0:
                        line = line[reg_erg.start():]
                    date = reg_erg.group()
                    amount = re.search('-*\d*(\.)*\d+,{1}\d{2}', line).group().replace('.', '').replace(',', '.')
                    line = line.replace(date, '').replace(re.search('-*\d*\.*\d+,{1}\d{2}', line).group(), '').replace(
                        ',', ';')
                    category, purpose = get_category_purpose(line)
                    #print(date + ', ' + amount + ', ' + category + ', ' + purpose)
                    writer.writerow([date, amount, category, purpose])
        file.close()


def get_category_purpose(line):
    category = 'undefined'
    purpose = 'undefined'
    for key in keywords:
        if key in line:
            category = key
            purpose = line.replace(key, '').strip()
    return category, purpose


if __name__ == "__main__":
    user_provided_path = '/Users/...'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:")#, ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('you need to pass an argument in the form: test.py -i <inputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile>')
            sys.exit()
        elif opt == '-i':
            user_provided_path = arg
    print('Input file is: ', user_provided_path)

    if os.path.isdir(user_provided_path):
        for filename in os.listdir(user_provided_path):
            print(user_provided_path + '/' + filename)
            convert_file(user_provided_path + '/' + filename)
        print("folder converted sucessfully")
    elif os.path.isfile(user_provided_path):
        convert_file(user_provided_path)
        print("file converted succesfully")
    else:
        print("Ooops something went wrong. Check that the path you provide is valid and redirects either to a .pdf or "
              "a directory with only pdfs.")
    sys.exit()
