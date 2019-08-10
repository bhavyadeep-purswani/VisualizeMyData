from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import MySQLdb
from bokeh.io import show, output_file, curdoc
from bokeh.models import ColumnDataSource, FactorRange,Slider, CustomJS
from bokeh.plotting import figure
from bokeh.embed import components,json_item
from bokeh.layouts import row, column
from bokeh.core.properties import value
from bokeh.transform import dodge            
import json

app = Flask(__name__)

app.secret_key="mykey";
@app.route('/VisualizeMyData',methods=['GET'])
def VisualizeMyData():
	if 'login' in session:
		return redirect(url_for("displayDatabases"))
	if 'loginError' in session:
		e=session['loginError']
	else:
		e=""
	return render_template("home.html",error=e)
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=='POST':
		form = request.form
		try:
			db = MySQLdb.connect(host="localhost",user=form['username'],passwd=form['password'])
			db.close()
			session['login']=True
			session['dbUsername']=form['username']
			session['dbPassword']=form['password']
			if 'loginError' in session:
				session.pop('loginError',None)
			return redirect(url_for("displayDatabases"))
		except:
			session['loginError']="Wrong username or password"
			return redirect(url_for("VisualizeMyData"))
	else:
		return redirect(url_for("VisualizeMyData"))
@app.route('/VisualizeMyData/logout')
def logout():
	session.clear()
	return redirect(url_for("VisualizeMyData"))
@app.route('/execute',methods=['POST'])
def executeSQL():
	if request.method=="POST":
		form=request.form
		db = MySQLdb.connect(host="localhost",user=session['dbUsername'],passwd=session['dbPassword'],db=form['database'])
		cursor=db.cursor()
		cursor.execute("desc "+form['table'])
		data = cursor.fetchall()
		l=[]
		response=dict()
		for i in data:
			l.append(i[0])
		if not form['xVal'] in l or not form['yVal'] in l:
			response['error']="Invalid X or Y value!"
			return jsonify(response)
		response['error']=""
		cursor.execute("select "+form['xVal']+" from "+form['table'])
		data = cursor.fetchall()
		x=[i[0] for i in data]
		cursor.execute("select "+form['yVal']+" from "+form['table'])
		data = cursor.fetchall()
		y=[i[0] for i in data]
		data = {"X":x,"Y":y}
		source = ColumnDataSource(data=data)
		p = figure(x_range=x, plot_height=350, plot_width=1200)
		p.vbar(x=dodge('X',  0.0,  range=p.x_range), top='Y', width=0.2, source=source, color="#718dbf")
		p.xaxis[0].axis_label = form['xVal']
		p.yaxis[0].axis_label = form['yVal']
		response["item_text"]=json.dumps(json_item(p))
		db.commit()
		db.close()
		return jsonify(response)
@app.route('/databases')
def displayDatabases():
	if 'login' not in session:
		return redirect(url_for("VisualizeMyData"))
	db = MySQLdb.connect(host="localhost",user=session['dbUsername'],passwd=session['dbPassword'])
	cursor = db.cursor()
	cursor.execute("Show databases")
	databases = cursor.fetchall()
	cursor.close()
	db.close()
	return render_template("displayDatabases.html",databases=databases)
@app.route('/databases/<database>')
def displayTables(database):
	if 'login' not in session:
		return redirect(url_for("VisualizeMyData"))
	db = MySQLdb.connect(host="localhost",user=session['dbUsername'],passwd=session['dbPassword'])
	cursor = db.cursor()
	cursor.execute("Show databases")
	databases = cursor.fetchall()
	if not (database,) in databases:
		return redirect(url_for("displayDatabases"))
	cursor.execute("use "+database)
	cursor.execute("show tables")
	tables = cursor.fetchall()
	cursor.close()
	db.close()
	return render_template("displayTables.html",database=database,tables=tables)
@app.route('/databases/<database>/<table>')
def displayRows(database,table):
	if 'login' not in session:
		return redirect(url_for("VisualizeMyData"))
	db = MySQLdb.connect(host="localhost",user=session['dbUsername'],passwd=session['dbPassword'])
	cursor = db.cursor()
	cursor.execute("Show databases")
	databases = cursor.fetchall()
	if not (database,) in databases:
		return redirect(url_for("displayDatabases"))
	cursor.execute("use "+database)
	cursor.execute("show tables")
	tables = cursor.fetchall()
	if not (table,) in tables:
		return redirect(url_for("displayDatabases")+"/"+database)
	cursor.execute("desc "+table);
	rows=cursor.fetchall()
	cursor.close()
	db.close()
	return render_template("displayPlots.html",database=database,rows=rows,table=table)
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response
app.after_request(add_cors_headers)
app.run()
