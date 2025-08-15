import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    df = pd.read_csv('C:\\Users\\george\\source\\repos\\MyFunds\\data\\申万行业10周动量看板.csv')
    return render_template('dashboard.html', table=df.to_html(classes='altrowstable'))

if __name__ == '__main__':
    app.run(debug=True)