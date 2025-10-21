from flask import Flask, render_template, jsonify,request
import random
app = Flask(__name__)
destination = ""

@app.route('/')
def home():
    return render_template('mainui.html')

@app.route('/data')
def data():
    speed = random.randint(0,30)
    car_state= "MOVING" if speed else "STATIONARY"
    return jsonify({'speed': speed,'destination':destination,'car_state':car_state})

@app.route('/update_destination', methods=['POST'])
def update_destination():
    global destination,location
    data =  request.get_json()
    destination = data.get('destination') 
    response = {'destination': destination}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)




       