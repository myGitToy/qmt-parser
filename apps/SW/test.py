from flask import Flask, request, render_template, redirect, url_for
app = Flask(__name__)

# 假设我们的自选股存储在这个列表中
stocks = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 添加股票
        if 'add' in request.form:
            stock = request.form.get('stock')
            if stock and stock not in stocks:
                stocks.append(stock)
        # 删除股票
        elif 'delete' in request.form:
            stock = request.form.get('stock')
            if stock in stocks:
                stocks.remove(stock)
    return render_template('index.html', stocks=stocks)
@app.route('/delete/<stock>')
def delete(stock):
    if stock in stocks:
        stocks.remove(stock)
    return redirect(url_for('index'))

@app.route('/view/<stock>')
def view(stock):
    # 这里你可以添加查看股票的逻辑
    return '查看股票: ' + stock
if __name__ == '__main__':
    app.run(debug=True)