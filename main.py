import numpy as np
import streamlit as st
import easyocr
import cv2
import re
from PIL import Image
#initalize the reader
reader = easyocr.Reader(['en'])
def easyocr_predicted(img):
    image_text =  reader.readtext(img) # it takes 1 minutes 35 seconds
    print(image_text)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for detection in image_text:
        top_left = tuple(detection[0][0])
        bottom_right = tuple(detection[0][2])
        text = detection[1]
        img = cv2.rectangle(img,top_left,bottom_right,(0,255,0),3)
        img = cv2.putText(img,text,top_left, font, 5,(255,0,0),5,cv2.LINE_AA)
    return image_text,img

def main_ocr(img):
    output_text,img = easyocr_predicted(img)
    result="" # an empty string
    for single_output in output_text:
        #structure of single_output ->  ([[681, 314], [1603, 314], [1603, 527], [681, 527]], 'BANNARI', 0.9994982510354642)
        # a tuple -> 0th index-coordinates(top_right,top_left,bottom_right,bottom_left)
        #1st index - predicted text
        #2nd or last index -> confidence score
        if single_output[-1] > 0.5:
            result += single_output[1]+'\n'
        else:
            top_left = single_output[0][0] # [681, 314]
            bottom_left = single_output[0][-1]
            top_right = single_output[0][1]
            height = bottom_left[1] - top_left[1] #to find the height of the predicted segment
            width = top_right[0] - top_left[0] #to find the height of the predicted segment
            print(height,width)
            if height > 1000 or height > width*2 : #([[278, 1059], [547, 1059], [547, 2195], [278, 2195]], '0', 0.36467499949708326)
                cropped_result = post_processing(single_output,img) #[([[9, 0], [1133, 0], [1133, 247], [9, 247]], '2021-2025', 0.9998907497931622)]
                for i in cropped_result: # i -> ([[9, 0], [1133, 0], [1133, 247], [9, 247]], '2021-2025', 0.9998907497931622)
                    if i[-1] > 0.5:
                        result+=i[1]+'\n' #'2021-2025'
                    else:
                        continue
            else :
                continue
    print(result)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    return result,img

def post_processing(single_output,img):
    row_start = single_output[0][0][1]
    row_end = single_output[0][-1][1]
    col_start = single_output[0][0][0]
    col_end = single_output[0][1][0]
    cropped = img[row_start:row_end,col_start:col_end]#cropping the image # [rows->y axis, columns -> x axis]
    cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
    cropped_result,img = easyocr_predicted(cropped)
    return cropped_result

def front_text_classification(image_front_text):
    batch=""
    if re.findall(r'\d{4}-\d{4}',image_front_text)!=[]:
        batch = re.findall(r'\d{4}-\d{4}',image_front_text)[0] #['2021-2025'] -> 2021-2025
    name = re.findall(r'\d{4}-\d{4}\n(.*)|(.*)\n\d{7}\D{2}\d{3}',image_front_text)[0] # based on the roll no or batch
    roll_no = re.findall(r'\d{7}\D{2}\d{3}',image_front_text)[0] #7376212al114
    degree = re.findall(r'\D\..*\.',image_front_text)[0] #B.Tech. or B.E.
    department = re.findall(r'\D\..*\.\n(.*)',image_front_text)[0] #AIML -> depended on degree
    accomodation = re.findall(r'\D\..*\.\n.*\n(\D)',image_front_text)[0] # -> depended on degree and department
    if accomodation == 'H':
        accomodation = "Hosteller"
    elif accomodation == 'D':
        accomodation = "Day Scholar"

    final =f"""
    Name              : {name}
    Roll NO           : {roll_no}
    Degree            : {degree}
    Department        : {department}
    Batch             : {batch}
    Accomodation Type : {accomodation}
        """
    return final

def back_text_classification(image_back_text):
    dob = re.findall(r'D.O.B\n(.*)|DOB :\n(.*)|D.O.B :\n(.*)',image_back_text)[0]
    for i in dob:
        print(i)
        if i!="":
            dob=i
            break
    blood = re.findall(r'B.G\n(.*)|B.G :\n(.*)|BG :\n(.*)',image_back_text)[0]
    for i in blood:
        if i!="":
            blood=i
            break
    address = re.findall(r'ADDRESS\n((\n|.)*)STUDENT PHONE|ADDRESS :\n((\n|.)*)STUDENT PHONE',image_back_text)[0] # 0th index -> ('SIO, SELVARAJ M\n239,GURU TEX COMPLEXKA-\nLIYAMMAN KOVIL\nELAMPILLAI\nSANKAGARI\nSALEM\n637502\n', '\n')
    for i in address:
        if i != "":
            address = i
            break
    stu_num = re.findall(r'STUDENT PHONE\n(\d{10})|STUDENT PHONE :\n(\d{10})',image_back_text)[0]
    for i in stu_num:
        if i != "":
            stu_num = i
            break
    par_num = re.findall(r'PARENT PHONE\n(\d{10})|PARENT PHONE :\n(\d{10})',image_back_text)[0]
    for i in par_num:
        if i != "":
            par_num = i
            break
    print(image_back_text)
    email=""
    if re.findall(r'.*@.*',image_back_text) !=[]:
        email = re.findall(r'.*@.*',image_back_text)[0]
    final = f"""
    Blood Group    : {blood}
    Date Of Birth  : {dob}
    Student Number : {stu_num}
    Parent Number  : {par_num}
    Official Email : {email}
    Address        : {address}
    """
    return final
#image_back_text=main_ocr(image_back)

if __name__ == "__main__":
    # to change the title and icon
    st.set_page_config(page_title="ExtraID", page_icon="🪪", layout="wide", initial_sidebar_state="collapsed")
    st.markdown("<h1 style='text-align: center;'>Extract the data in ID card 🪪</h1>", unsafe_allow_html=True)
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
            st.code(front_text_classification(image_front_text))
    with col2:
        st.markdown('<h3 style="text-align: center;margin-top:2rem;">Back side</h3>',
                    unsafe_allow_html=True)
        image_back = st.file_uploader("Choose Back Side Image of ID card")
        if image_back:
            image_back = Image.open(image_back)
            image_back = np.array(image_back)
            image_back_text,img_back_pred = main_ocr(image_back)
            st.image(img_back_pred)
            st.subheader("Extracted Text of Back Side")
            st.text(image_back_text)
            st.subheader("Classified Text of Back Side")
            st.code(back_text_classification(image_back_text))