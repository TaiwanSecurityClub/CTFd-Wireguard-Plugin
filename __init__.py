from CTFd.models import db
from CTFd.utils.decorators import authed_only,get_current_user,admins_only
from CTFd.plugins import register_plugin_assets_directory
from CTFd.models import Users

#from flask import request,render_template

from pathlib import Path

import flask
import io
import os
import yaml
import requests
import zipfile
import urllib.parse

conf = None
plugin_name = __name__.split('.')[-1]

class WireguardDB(db.Model):
    __tablename__ = "wireguardDB"
    userid = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    key = db.Column(db.String(128))
    index = db.Column(db.Integer, primary_key = True, autoincrement=True)

    def __init__(self, userid):
        self.userid = userid
        self.key = None
        for a in conf:
            try:
                res = requests.get(urllib.parse.urljoin(a['url'], 'genkey'), headers={"Authorization": f"Token {conf[0]['key']}"}, timeout=2)
                if res.status_code == 200:
                    self.key = res.text
                    break
            except:
                pass
        if self.key is None:
            raise Exception("Apis not work")

    def getusername(self):
        return Users.query.filter_by(id=self.userid).first().name

def loadconfig():
    global conf
    dir_path = Path(__file__).parent.resolve()
    with open(os.path.join(dir_path, 'config.yml')) as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

def load(app):
    app.db.create_all()
    loadconfig()

    register_plugin_assets_directory(app, base_path=f'/plugins/{plugin_name}/assets')
    
    @admins_only
    @app.route(f'/plugins/{plugin_name}/getuserid',methods=['POST'])
    def getuserid():
        data = flask.request.get_json()
        privkey = WireguardDB.query.filter_by(index=data['index']).first()
        if privkey == None:
            return flask.jsonify(None)

        return flask.jsonify(privkey.userid)
    
    @authed_only
    @app.route(f'/plugins/{plugin_name}/download',methods=['GET'])
    def download():
        user = get_current_user()
        try:
            WireguardDB.query.filter_by(userid=user.id).one()
        except:
            db.session.add(WireguardDB(user.id))
            db.session.commit()
        
        alluserpriv = WireguardDB.query.all()
        alluserpriv = [{'name': userpriv.getusername(), 'key': userpriv.key, 'index': userpriv.index} for userpriv in alluserpriv]
        for a in conf:
            try:
                requests.post(urllib.parse.urljoin(a['url'], 'reload'), headers={"Authorization": f"Token {conf[0]['key']}"}, json=alluserpriv, timeout=2).text
            except:
                pass

        privkey = WireguardDB.query.filter_by(userid=user.id).first()
        privkey = {'name': privkey.getusername(), 'key': privkey.key, 'index': privkey.index}

        sendfile = io.BytesIO()
        with zipfile.ZipFile(sendfile, 'w') as myzip:
            for a in conf:
                try:
                    res = requests.post(urllib.parse.urljoin(a['url'], 'getconfig'), headers={"Authorization": f"Token {conf[0]['key']}"}, json=privkey, timeout=2)
                    if res.status_code == 200:
                        userconfig = res.text
                        myzip.writestr(f"{a['name']}.conf", userconfig)
                except:
                    pass

        sendfile.seek(0)
        return flask.Response(sendfile.getvalue(), mimetype='application/zip', headers={'Content-Disposition': 'attachment;filename=vpnconfig.zip'})
            
