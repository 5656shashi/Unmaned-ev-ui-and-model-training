from flask import Flask, render_template, jsonify,request
import random
#import SerialMaster
app = Flask(__name__)
destination = ""
started=False
def init():
    global started
    print("init Attempt")
    if started:
        return
    #SerialMaster.setupArduino()
    started=True
@app.route('/')
def home():
    init()
    return render_template('mainui.html')

@app.route('/data')
def data():
    init()
    #angle = SerialMaster.readAngle()
    #speed = SerialMaster.readSpeed()                                                                       
    speed=10 
    car_state= "MOVING" if speed else "STATIONARY"
    return jsonify({'speed': speed,'destination':destination,'car_state':car_state})

@app.route('/update_destination', methods=['POST'])
def update_destination():
    init()
    global destination
    data =  request.get_json()
    destination = data.get('destination') 
    response = {'destination': destination}
    return jsonify(response)

if __name__ == '__main__':
    # init()
    app.run(debug=True)




       