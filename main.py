import streamlit as st
from google.cloud import vision
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pandas as pd
import cv2
import re

# skincare products dataset (Sephora)
df = pd.read_csv('Dataset/skincare_dataset_final.csv', sep = ';')

#brands available in the dataset
brands = df['Brand'].drop_duplicates().reset_index(drop = True)

# ingredient dictionary
dic = pd.read_csv('Dataset/ingredient_dictionary_update.csv', sep = ';')

def detect_product(content):
#   content = fileup.read()
  client = vision.ImageAnnotatorClient()
  image = vision.Image(content=content)
  response = client.text_detection(image=image)
  texts = response.text_annotations
#   st.write(texts)
  text_raw = texts[0].description
  text_lean = re.sub('\n', ' ', text_raw)
  brand_probas = []
  for i in brands:
      partial_ratio = fuzz.partial_ratio(i.lower(),text_raw.lower())
      brand_probas.append(partial_ratio)
  if max(brand_probas) > 70:
      des_probas = []
      max_index = brand_probas.index(max(brand_probas))
      brand = brands[max_index]
      df_filtered = df[df.Brand == brand]
      for des in df_filtered.Name:
          des_ratio = fuzz.token_set_ratio(text_lean, des)
          des_probas.append(des_ratio)
      if max(des_probas) > 50:
          des_index = des_probas.index(max(des_probas))
          result_line = df_filtered.iloc[des_index]
          # st.dataframe(result_line.astype(str))  show df from pandas series 
          st.write(f'Top match item found: {max(des_probas) * max(brand_probas)/100}%')
          st.write(f'Brand: {result_line.Brand}')
          st.write(f'Description: {result_line.Name}')
          st.write(f'Price: ${result_line.Price}')
          st.write(f'Rating: {result_line.Rank}/5')
          skin = ['Sensitive', 'Dry', 'Normal', 'Combination', 'Body']
          skin_type = [i for i in skin if result_line[i]>0]
          st.write(f'Skin Type: {skin_type}')
          st.write(f'INGREDIENT DECODING:')
          decoding_dic = {}
          decoding_dic['Ingredient'] = []
          decoding_dic['% Match'] = []
          decoding_dic['Match Item'] = []
          decoding_dic['Index'] = []
          for i in map(lambda x: x.strip(), result_line.Ingredients.split(',')):
              item, proba, index = process.extractOne(i,dic.name)
              decoding_dic['Ingredient'].append(i)
              decoding_dic['% Match'].append(proba)
              decoding_dic['Match Item'].append(item)
              decoding_dic['Index'].append(index)
          decoding_df = pd.DataFrame.from_dict(decoding_dic)
          final_df = decoding_df.merge(dic, how = 'left', left_on = decoding_df['Index'], right_index = True)
          final_df.drop(columns = ['Index', 'name'], inplace = True)
          st.dataframe(final_df)
      else:
          st.write("Sorry, I couldn't find any match. Would you like to try again? Make sure brand name and product description are readable. Or you call fill such info in the below.")
  else:
      st.swrite("Sorry, I couldn't find any match. Would you like to try again? Make sure brand name and product description are readable. Or you call fill such info in the below.") 

st.image('streamlit_mysa.PNG')
st.write("Hi, there! I will be your skincare assistant here. So how do I assist you when it comes to skincare? You just need to give me some photo taken with the front packaging of your inquired skincare product. For each photo, I will tell you what I know about it's price, consumer rating, and most important - I help decode the ingredient list into the language you can understand: What are they for? How do they work? Are they safe?")
st.write("I will try my best to constantly update my knowledge to response to all your product inqueries. However, we may encounter problem of product info or ingredient not found. In such case, I will save your input photo and work on it as soon as I can.")
st.write("👩🏻‍⚕️ Remember never rely on one single (online!) source to make important decisions. If you have serious skin problems/concerns, please visit your dermatologist for adequate advisory.")
st.subheader("Let's start! Take or upload photo of product's front label.")
st.write('Make sure brand name and a short description are readable from the photo.')

st.caption('TAKE PHOTO')
cap = cv2.VideoCapture(0)
run = st.checkbox('Open Camera')
capture_button = st.button('Capture')

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

FRAME_WINDOW = st.image([])
while run:
    ret, frame = cap.read()        
    # Display Webcam
    #frame = cv2.flip(frame, 1)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB ) #Convert color
    FRAME_WINDOW.image(frame)

    if capture_button: # to capture
        captured_image = frame
        if  captured_image.all() != None:
            content_cam = captured_image.tobytes()
            detect_product(content_cam)
            break
        #st.image(captured_image)

cap.release()

fileup = st.file_uploader('OR UPLOAD FILE', type = ['jpg', 'png', 'jpeg'])
if fileup != None:  
    st.image(fileup)
    content_up = fileup.read()
    # st.write(content_up)
    detect_product(content_up)

st.subheader("You can also search for product by ")
