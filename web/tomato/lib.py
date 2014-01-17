# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.http import HttpResponse
from django.shortcuts import render, redirect
import xmlrpclib, json, urllib, socket
import settings 

def getauth(request):
	auth = request.session.get("auth")
	if not auth:
		return None
	username, password = auth.split(':',1)
	return (username, password)

class AuthError(Exception):
	pass

class ServerProxy(object):
	def __init__(self, url, **kwargs):
		self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)
	def __getattr__(self, name):
		call_proxy = getattr(self._xmlrpc_server_proxy, name)
		def _call(*args, **kwargs):
			return call_proxy(args, kwargs)
		return _call

def getapi(request=None):
	auth=None
	if request:
		auth=getauth(request)
	if auth:
		(username, password) = auth
		username = urllib.quote_plus(username)
		password = urllib.quote_plus(password)
	try:
		if auth:
			api = ServerProxy('%s://%s:%s@%s:%s' % (settings.server_protocol, username, password, settings.server_host, settings.server_port), allow_none=True )
			api.user = UserObj(api)
		else:
			api = ServerProxy('%s://%s:%s' % (settings.server_protocol, settings.server_host, settings.server_port), allow_none=True )
			api.user = None
	except:
		api = ServerProxy('%s://%s:%s' % (settings.server_protocol, settings.server_host, settings.server_port), allow_none=True )
		api.user = None
	if request:
		request.session.user = api.user
	return api

class wrap_rpc:
	def __init__(self, fun):
		self.fun = fun
		self.__name__ = fun.__name__
		self.__module__ = fun.__module__
	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			return self.fun(api, request, *args, **kwargs)
		except Exception, e:
			import traceback
			traceback.print_exc()
			if isinstance(e, socket.error):
				import os
				etype = "Socket error"
				ecode = e.errno
				etext = os.strerror(e.errno)
			elif isinstance(e, AuthError):
				request.session['forward_url'] = request.build_absolute_uri()
				return redirect("tomato.main.login")
			elif isinstance(e, xmlrpclib.ProtocolError):
				etype = "RPC protocol error"
				ecode = e.errcode
				etext = e.errmsg
				if ecode in [401, 403]:
					request.session['forward_url'] = request.build_absolute_uri()
					return redirect("tomato.main.login")
			elif isinstance(e, xmlrpclib.Fault):
				etype = "RPC call error"
				ecode = e.faultCode
				etext = e.faultString
			else:
				etype = e.__class__.__name__
				ecode = ""
				etext = e.message
			return render(request, "main/error.html", {'type': etype, 'code': ecode, 'text': etext}, status=500)
		
class wrap_json:
	def __init__(self, fun):
		self.fun = fun
	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			data = json.loads(request.REQUEST["data"]) if request.REQUEST.has_key("data") else {}
			data.update(kwargs)
			try:
				res = self.fun(api, *args, **data)
				return HttpResponse(json.dumps({"success": True, "result": res}))
			except xmlrpclib.Fault, f:
				return HttpResponse(json.dumps({"success": False, "error": f.faultString}))
			except xmlrpclib.ProtocolError, e:
				return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (e.errcode, e.errmsg)}), status=e.errcode if e.errcode in [401, 403] else 200)				
			except Exception, exc:
				return HttpResponse(json.dumps({"success": False, "error": '%s:%s' % (exc.__class__.__name__, exc)}))				
		except xmlrpclib.ProtocolError, e:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (e.errcode, e.errmsg)}), status=e.faultCode if e.faultCode in [401, 403] else 200)				
		except xmlrpclib.Fault, f:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s' % f}))

DEVNULL = open("/dev/null", "w")

def runUnchecked(cmd, shell=False, ignoreErr=False, input=None, cwd=None): #@ReservedAssignment
	import subprocess
	stderr = DEVNULL if ignoreErr else subprocess.STDOUT
	stdin = subprocess.PIPE if input else None
	proc=subprocess.Popen(cmd, cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr, shell=shell, close_fds=True)
	res=proc.communicate(input)
	return (proc.returncode,res[0])

def getDpkgVersionStr(package):
	fields = {}
	error, output = runUnchecked(["dpkg-query", "-s", package])
	if error:
		return None 
	for line in output.splitlines():
		if ": " in line:
			name, value = line.split(": ")
			fields[name.lower()] = value
	if not "installed" in fields["status"]:
		return None
	return fields["version"]

def splitVersion(verStr):
	version = []
	numStr = ""
	if not verStr:
		return verStr
	for ch in verStr:
		if ch in "0123456789":
			numStr += ch
		if ch in ".:-":
			version.append(int(numStr))
			numStr = ""
	version.append(int(numStr))
	return version
	
def getDpkgVersion(package, verStr=None):
	verStr = getDpkgVersionStr(package)
	return splitVersion(verStr)

def getVersion():
	return getDpkgVersion("tomato-web") or "devel"

class UserObj:
	def __init__(self, api):
		self.data = api.account_info()
		self.name = self.data["name"]
		self.flags = self.data["flags"]
		self.origin = self.data["origin"]
		self.organization = self.data["organization"]
		self.realname = self.data["realname"]
	def hasGlobalToplFlags(self):
		for flag in ["global_topl_admin", "global_topl_manager", "global_topl_user"]:
			if flag in self.flags:
				return True
		return False
	def hasOrgaToplFlags(self):
		for flag in ["orga_topl_admin", "orga_topl_manager", "orga_topl_user"]:
			if flag in self.flags:
				return True
		return False
	def isAdmin(self, orgaName=None):
		if "global_admin" in self.flags:
			return True
		if "orga_admin" in self.flags and self.organization == orgaName:
			return True
		return False
	def isHostManager(self, orgaName=None):
		if "global_host_manager" in self.flags:
			return True
		if "orga_host_manager" in self.flags and self.organization == orgaName:
			return True
		return False