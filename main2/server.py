from flask import Flask, request, jsonify, render_template
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd

app = Flask(__name__)

# Load the data and models
df = pd.read_csv("disease_description.csv")
specialist_df = pd.read_csv("specialist_description.csv")

tokenizer = AutoTokenizer.from_pretrained("23tanmay/BioDistillGPT2")
model = AutoModelForCausalLM.from_pretrained("23tanmay/BioDistillGPT2")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    input_prompt = request.json.get("symptoms", "")
    
    # Tokenize the input prompt
    input_ids = tokenizer.encode(input_prompt, return_tensors="pt")
    output_ids = model.generate(
        input_ids,
        max_length=800,
        num_return_sequences=3,
        top_p=0.95,
        top_k=50,
        do_sample=True
    )

    response = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    response2 = tokenizer.decode(output_ids[1], skip_special_tokens=True)
    response3 = tokenizer.decode(output_ids[2], skip_special_tokens=True)
    response_string = response + response2 + response3

    scores = {}

    response_words = response_string.lower().split()

    for word in response_words:
        for index, row in specialist_df.iterrows():
            if word == row['Speciality'].lower() and word != "medicine" and word != "and":
                scores[row['Speciality']] = scores.get(row['Speciality'], 0) + 1000
            elif row['Speciality'].lower().endswith("ogy"):
                specialty_term = row['Speciality'].lower()[:-3] + "ogist"
                if specialty_term in response_string.lower():
                    scores[row['Speciality']] = scores.get(row['Speciality'], 0) + 1000

    for index, row in specialist_df.iterrows():
        description_words = row['Description'].lower().split()
        for word in description_words:
            if word in response_words:
                scores[row['Speciality']] = scores.get(row['Speciality'], 0) + 5

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    top_specialists = [{"speciality": speciality, "score": score} for speciality, score in sorted_scores[:3]]

    return jsonify({"top_specialists": top_specialists})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
