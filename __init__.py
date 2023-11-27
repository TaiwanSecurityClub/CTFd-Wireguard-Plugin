from CTFd.models import db
from CTFd.utils.decorators import authed_only,get_current_user

#from flask import request,render_template

from pathlib import Path

import flask
import io
import os
import yaml
import requests
import zipfile

conf = None

class WireguardDB(db.Model):
    name = db.Column(db.String(128), primary_key = True)
    key = db.Column(db.String(128))
    index = db.Column(db.Integer, primary_key = True, autoincrement=True)

    def __init__(self, name):
        self.name = name
        self.key = requests.get(f"{conf[0]['url']}/genkey").text

def loadconfig():
    global conf
    dir_path = Path(__file__).parent.resolve()
    with open(os.path.join(dir_path, 'config.yaml')) as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

def load(app):
    app.db.create_all()
    loadconfig()
    
    @authed_only
    @app.route('/wireguard/download',methods=['GET'])
    def download():
        user = get_current_user()
        try:
            WireguardDB.query.filter_by(name=user.name).one()
        except:
            db.session.add(WireguardDB(user.name))
            db.session.commit()
            alluserpriv = WireguardDB.query.all()
            alluserpriv = [{'name': userpriv.name, 'key': userpriv.key, 'index': userpriv.index} for userpriv in alluserpriv]
            for a in conf:
                requests.post(f"{a['url']}/reload", json=alluserpriv).text

        privkey = WireguardDB.query.filter_by(name=user.name).first()
        privkey = {'name': privkey.name, 'key': privkey.key, 'index': privkey.index}

        sendfile = io.BytesIO()
        with zipfile.ZipFile(sendfile, 'w') as myzip:
            for a in conf:
                userconfig = requests.post(f"{a['url']}/getconfig", json=privkey).text
                myzip.writestr(f"{a['name']}.conf", userconfig)

        sendfile.seek(0)
        return flask.Response(sendfile.getvalue(), mimetype='application/zip', headers={'Content-Disposition': 'attachment;filename=vpnconfig.zip'})
            
