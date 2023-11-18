import numpy as np
import streamlit as st
import easyocr
import cv2
import re
from PIL import Image
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from time import ctime
# initalize the reader
reader = easyocr.Reader(['en'])


#https://colab.research.google.com/drive/1-MKuJNyAiUpeVZtf98ApLSzp6KTFGz-_#scrollTo=Je6ka6rrx8Wx&uniqifier=1


# idcard@idcard-405217.iam.gserviceaccount.com

# Function to append a list as a row to Google Sheet
def append_to_google_sheet(data):
    # Load Google Sheets API credentials from the JSON file
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('./idcard-405217-79628c52f4d1.json', scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet by title
    sheet = client.open('Id card ocr datas').sheet1

    # Append the lsit as a row to the sheet
    sheet.append_row(data)


def easyocr_predicted(img):
    image_text = reader.readtext(img)  # it takes 1 minutes 35 seconds based on the computation power
    # print(image_text)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for detection in image_text:
        top_left = tuple([int(x) for x in detection[0][
            0]])  # ([[682).1135155856441, 839.0994685768342], [768.8559704728243, 851.9362840074967], [761.8864844143559, 890.9005314231658], [674.1440295271757, 878.0637159925033]], 'Sat', 0.007399932870564301)]
        bottom_right = tuple([int(x) for x in detection[0][2]])
        text = detection[1]
        # print(top_left,bottom_right)
        img = cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 3)
        img = cv2.putText(img, text, top_left, font, 5, (255, 0, 0), 5, cv2.LINE_AA)
    # cv2_imshow(img)
    return image_text, img


def main_ocr(img):
    output_text, predicted_img = easyocr_predicted(img)
    result = ""  # an empty string
    for single_output in output_text:
        # structure of single_output ->  ([[681, 314], [1603, 314], [1603, 527], [681, 527]], 'BANNARI', 0.9994982510354642)
        # a tuple -> 0th index-coordinates(top_right,top_left,bottom_right,bottom_left)
        # 1st index - predicted text
        # 2nd or last index -> confidence score
        top_left = single_output[0][0]  # [681, 314]
        bottom_left = single_output[0][-1]
        top_right = single_output[0][1]
        height = bottom_left[1] - top_left[1]  # to find the height of the predicted segment
        width = top_right[0] - top_left[0]  # to find the height of the predicted segment
        if height > 1000 or height > width * 2 or height > width * 1.8:  # ([[278, 1059], [547, 1059], [547, 2195], [278, 2195]], '0', 0.36467499949708326):
            # print(height,width)
            cropped_result = post_processing(single_output, img,
                                             rotate_option="clock")  # [([[9, 0], [1133, 0], [1133, 247], [9, 247]], '2021-2025', 0.9998907497931622)]
            print(cropped_result, "cc")
            for i in cropped_result:  # i -> ([[9, 0], [1133, 0], [1133, 247], [9, 247]], '2021-2025', 0.9998907497931622)
                if i[-1] > 0.5:
                    result += i[1] + '\n'  # '2021'
                else:
                    cropped_result2 = post_processing(single_output, img, rotate_option="counter_clock")
                    print(cropped_result2, "cc")
                    for j in cropped_result2:  # i -> ([[9, 0], [1133, 0], [1133, 247], [9, 247]], '2021-2025', 0.9998907497931622)
                        if j[-1] > 0.5:
                            result += j[1] + '\n'  # '2021-2025'
        elif single_output[-1] > 0.5:
            print("perfect : ", single_output)
            result += single_output[1] + '\n'
    print(result)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return result, predicted_img


def post_processing(single_output, img, rotate_option):
    row_start = single_output[0][0][1]
    row_end = single_output[0][-1][1]
    col_start = single_output[0][0][0]
    col_end = single_output[0][1][0]
    cropped = img[row_start:row_end, col_start:col_end]  # cropping the image # [rows->y axis, columns -> x axis]
    if rotate_option == 'clock':
        cropped = cv2.rotate(cropped, cv2.ROTATE_90_CLOCKWISE)
    elif rotate_option == 'counter_clock':
        cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
    # cv2_imshow(cropped)
    cropped_result, pred_img = easyocr_predicted(cropped)
    # cv2_imshow(pred_img)
    return cropped_result


def check_empty_return_value(arr):
    if arr == []:
        return ""
    if type(arr[0]) == str:  # ['7376212al114'] -> '7' == str
        return arr[0]
    arr = arr[0]  # due to the first index is the matched index in the group of regex
    if arr ==[]:
        return ""
    # for i in name:
    #     if i!="":
    #         name=i
    #         break
    return [name for name in arr if name != ""][0]  # shorthand for loop that stores result in list then print the 0th index


def front_text_classification(image_front_text):
    front_details_result = {'Name': "", 'Roll NO': "", "Degree": "", "Department": "", "Batch": '',
                            'Accomodation Type': ''}

    # ------------------------------ BATCH ---------------------------------
    temp_batch = re.findall(r'\d{4}-\d{4}|\d{4}\n\d{4}', image_front_text)
    temp_batch = [batch for batch in temp_batch if batch != ""]  # ['2027\n2023']
    # print("temp_batch",temp_batch)
    if temp_batch != []:
        if '-' in temp_batch[0]:
            front_details_result["Batch"] = temp_batch[0]  # ['2021-2025'] -> 2021-2025
        else:
            temp_batch = temp_batch[0]  # ['2025\n2021'] -> 2025\n2021
            temp_batch = temp_batch.split()  # ['2025','2021']
            front_details_result["Batch"] = temp_batch[1] + "-" + temp_batch[0]  # 2021-2025
    else:
        front_details_result["Batch"] = ""

    # -----------------------------  NAME ----------------------------------
    temp_name = re.findall(r'\d{4}-\d{4}\n(.*)|(.*)\n\d{7}\D{2}\d{3}',
                           image_front_text)  # based on the roll no or batch
    front_details_result["Name"] = check_empty_return_value(temp_name)

    # ---------------------------- ROLL NO ----------------------------------
    temp_roll_no = re.findall(r'\d{7}\D{2}\d{3}', image_front_text)  # ['7376212al114']
    front_details_result["Roll NO"] = check_empty_return_value(temp_roll_no)  # 7376212al114 or ""

    # ---------------------------- Degree ----------------------------------
    temp_degree = re.findall(r'\D\..*\.|\D\..*:|\D\D:', image_front_text)
    front_details_result["Degree"] = check_empty_return_value(temp_degree)[
                                     :-1]  # B.Tech. or B.E. or BE: or B.Tech: -> B.E or B.Tech

    # ---------------------------- Department ----------------------------------
    temp_department = re.findall(r'\D\..*\.\n(.*)|\D{2}:\n(.*)', image_front_text)
    front_details_result["Department"] = check_empty_return_value(temp_department)  # AIML -> depended on  degree

    # ---------------------------- Accomodation Type ----------------------------------
    temp_accomodation = re.findall(r'\n(H)\n|\n(D)\n', image_front_text)
    temp_accomodation = check_empty_return_value(temp_accomodation)  # H or D
    if temp_accomodation == 'H':
        front_details_result["Accomodation Type"] = "Hosteller"
    elif temp_accomodation == 'D':
        front_details_result["Accomodation Type"] = "Day Scholar"

    final = f"""
    Name              : {front_details_result["Name"]}
    Roll NO           : {front_details_result["Roll NO"]}
    Degree            : {front_details_result["Degree"]}
    Department        : {front_details_result["Department"]}
    Batch             : {front_details_result["Batch"]}
    Accomodation Type : {front_details_result["Accomodation Type"]}
        """
    return final, front_details_result


def back_text_classification(image_back_text):
    back_details_result = {"Blood Group": "", "Date Of Birth": "", "Student Number": "", "Parent Number": "",
                           "Official Email": "", "Address": ""}

    # ------------------------------- Date Of Birth ----------------------------
    temp_dob = re.findall(r'D.O.B\n(.*)|DOB :\n(.*)|D.O.B :\n(.*)|D.O.B.\n:\n(.*)|D.OB.*\n(.*)|\d{2}-\d{2}-\d{4}', image_back_text)
    back_details_result["Date Of Birth"] = check_empty_return_value(temp_dob)

    # ------------------------------- Blood Group ------------------------------
    temp_blood = re.findall(r'.+ve|.-ve', image_back_text)
    back_details_result["Blood Group"] = check_empty_return_value(temp_blood)

    # -------------------------------- Address ---------------------------------
    temp_address = re.findall(r'ADDRESS\n((\n|.)*)STUDENT PHONE|ADDRESS :\n((\n|.)*)STUDENT PHONE',
                              image_back_text)  # 0th index -> ('SIO, SELVARAJ M\n239,GURU TEX COMPLEXKA-\nLIYAMMAN KOVIL\nELAMPILLAI\nSANKAGARI\nSALEM\n637502\n', '\n')
    back_details_result["Address"] = check_empty_return_value(temp_address)

    # -------------------------------- Student Number --------------------------
    temp_stu_num = re.findall(r'STUDENT PHONE\n(\d{10})|STUDENT PHONE :\n(\d{10})', image_back_text)
    back_details_result["Student Number"] = check_empty_return_value(temp_stu_num)

    # -------------------------------- Parent Number --------------------------
    temp_par_num = re.findall(r'PARENT PHONE\n(\d{10})|PARENT PHONE :\n(\d{10})', image_back_text)
    back_details_result["Parent Number"] = check_empty_return_value(temp_par_num)

    # -------------------------------- Official Email --------------------------
    temp_email = re.findall(r'.*@.*', image_back_text)
    back_details_result["Official Email"] = check_empty_return_value(temp_email)

    final = f"""
Blood Group    : {back_details_result["Blood Group"]}
Date Of Birth  : {back_details_result["Date Of Birth"]}
Student Number : {back_details_result["Student Number"]}
Parent Number  : {back_details_result["Parent Number"]}
Official Email : {back_details_result["Official Email"]}
Address        : 
{back_details_result["Address"]}
    """
    return final, back_details_result


# image_back_text=main_ocr(image_back)

if __name__ == "__main__":
    # to change the title and icon
    st.set_page_config(page_title="ExtraID", page_icon="🪪", layout="wide", initial_sidebar_state="collapsed")
    st.markdown("<h1 style='text-align: center;'>Extract the data 📃 From ID card 🪪</h1>", unsafe_allow_html=True)
    # st.title("Extract the data in ID card 🪪")  # like h1 tag
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        st.markdown('<h3 style="text-align: center;margin-top:2rem;">Front side</h3>', unsafe_allow_html=True)
        image_front = st.file_uploader("Choose Front Side Image of ID card")
        if image_front:
            image_front = Image.open(image_front)
            image_front = np.array(image_front)
            image_front_text, img_front_pred = main_ocr(image_front)
            st.image(img_front_pred)
            st.subheader("Extracted Text of Front Side")
            st.text(image_front_text)
            st.subheader("Classified Text of Front Side")
            front_show_text, front_details_result = front_text_classification(image_front_text)
            st.code(front_show_text)


    with col2:
        st.markdown('<h3 style="text-align: center;margin-top:2rem;">Back side</h3>',
                    unsafe_allow_html=True)
        image_back = st.file_uploader("Choose Back Side Image of ID card")
        if image_back:
            image_back = Image.open(image_back)
            image_back = np.array(image_back)
            image_back_text, img_back_pred = main_ocr(image_back)
            st.image(img_back_pred)
            st.subheader("Extracted Text of Back Side")
            st.text(image_back_text)
            st.subheader("Classified Text of Back Side")
            back_show_text, back_details_result = back_text_classification(image_back_text)
            st.code(back_show_text)

            #sending the data to the gsheet

            full_details_push_to_gsheet = [ctime()]
            full_details_push_to_gsheet += list(front_details_result.values()) + list(back_details_result.values())
            print(full_details_push_to_gsheet)
            append_to_google_sheet(full_details_push_to_gsheet)

    # center the button
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        pass
    with col2:
        pass
    with col4:
        pass
    with col5:
        pass
    with col3:
        st.link_button("See all the data here 👉 ","https://docs.google.com/spreadsheets/d/183D8pChQlxFH1Km21KEke5olm-BmVVDgA0UFLxiY0j4/edit?usp=sharing")