from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
from datetime import datetime, date
import requests
import pygal
from pygal.style import LightColorizedStyle
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

stock_bp = Blueprint('stocks', __name__)

@stock_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@stock_bp.route('/visualize', methods=['POST'])
def visualize():
    symbol = request.form['symbol'].upper()
    chart_type = request.form['chart_type']
    time_series = request.form['time_series']
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", 'error')
        return redirect(url_for('stocks.index'))

    if start_date > end_date:
        flash("Start date must be before end date.", 'error')
        return redirect(url_for('stocks.index'))
    
    today = date.today()
    if start_date.date() > today or end_date.date() > today:
        flash("Dates cannot be in the future. Please select a valid date range.", 'error')
        return redirect(url_for('stocks.index'))

    data = fetch_stock_data(symbol, time_series)
    if not data or "Error Message" in data or "Note" in data:
        flash(f"'{symbol}' is not a valid stock symbol. Please try again.", 'error')
        return redirect(url_for('stocks.index'))
    
    time_series_key = next((k for k in data if "Time Series" in k), None)
    if not time_series_key:
        flash(f"No data available for '{symbol}'. Please try another stock.", 'error')
        return redirect(url_for('stocks.index'))

    dates, open_prices, high_prices, low_prices, close_prices = [], [], [], [], []
    for date_str, values in sorted(data[time_series_key].items()):
        try:
            current_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            if start_date <= current_date <= end_date:
                dates.append(current_date.strftime("%Y-%m-%d"))
                open_prices.append(float(values["1. open"]))
                high_prices.append(float(values["2. high"]))
                low_prices.append(float(values["3. low"]))
                close_prices.append(float(values["4. close"]))
        except:
            continue

    if not close_prices:
        flash("No data available in the selected date range.", 'error')
        return redirect(url_for('stocks.index'))

    chart = pygal.Bar(style=LightColorizedStyle, x_label_rotation=45, show_minor_x_labels=True) if chart_type == "Bar" else pygal.Line(style=LightColorizedStyle, x_label_rotation=45, show_minor_x_labels=True)
    chart.title = f"{symbol} Stock Data"
    step = max(1, len(dates) // 10)
    chart.x_labels = dates[::step]
    chart.x_labels_major = dates[::step]
    chart.add("Open", open_prices)
    chart.add("High", high_prices)
    chart.add("Low", low_prices)
    chart.add("Close", close_prices)

    if not os.path.exists("static"):
        os.makedirs("static")
    chart_path = "static/chart.svg"
    chart.render_to_file(chart_path)

    return render_template("index.html", chart=True, symbol=symbol, start=start_date, end=end_date, chart_path=chart_path)

def fetch_stock_data(symbol, function):
    API_KEY = "710QOQG2JW67UPY0"
    BASE_URL = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY,
        "datatype": "json"
    }
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = "60min"
    response = requests.get(BASE_URL, params=params)
    return response.json() if response.status_code == 200 else None

app.register_blueprint(stock_bp, url_prefix='/')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)