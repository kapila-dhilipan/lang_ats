from flask import Flask, render_template, request, jsonify
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from pymongo import MongoClient
import re
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Initialize the mongoDB Connection

mongo_uri = 'mongodb+srv://ssdev:ssdev123@ssdev.us8prjv.mongodb.net/test'

database_name = 'SSTEST'

collection_name = 'employees'

client = MongoClient(mongo_uri)

db = client[database_name]

collection = db[collection_name]

documents = collection.find()

df1 = pd.DataFrame(list(documents)).reset_index(drop=True)
df1 = df1.head(50)
data = df1.to_dict(orient='list')
df = pd.DataFrame(data)
df = df.head(50)
client.close()

# Initialize the language model
llm = ChatOpenAI(api_key="sk-proj-Xw84l7ZzVxIT37AmSK3MT3BlbkFJqGl8lEmsYagclNLSFcdk", model="gpt-3.5-turbo")

prompt_template = """
You are given an employee data table. Here is the data:
{data}

Please answer the following question based strictly on the data provided. Do not use any external information and don't add any explanation and add bulleted list.
Question:
{question}
"""

template = PromptTemplate(input_variables=["data", "question"], template=prompt_template)
chain = LLMChain(llm=llm, prompt=template)

def filter_response(response):
    # Remove any code-related content
    filtered_response = re.sub(r"```.*?```", "", response, flags=re.DOTALL)
    return filtered_response

def dict_to_html_table(data):
    # Convert dictionary to HTML table
    df = pd.DataFrame(data)
    return df.to_html(classes='dataframe table table-bordered table-hover', index=False)

# Route for the main page
# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/testing')
def index():
    return ('Working')
    
# Route for handling the chat
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    response = chain.invoke({"data": df.to_string(), "question": user_message})
    filtered_response = filter_response(response['text'])

    try:
        response_dict = json.loads(filtered_response)
        response_html = dict_to_html_table(response_dict)
        return jsonify({"response": response_html})
    except json.JSONDecodeError:
        response_points = filtered_response.split('\n')
        response_html = '<ul>'
        for point in response_points:
            if point.strip():
                response_html += f'<li>{point}</li>'
        response_html += '</ul>'
        return jsonify({"response": response_html})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
