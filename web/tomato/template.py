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
from django.shortcuts import render_to_response
from django.http import Http404

from lib import *
import xmlrpclib

@wrap_rpc
def index(api, request):
	return render_to_response("admin/template_index.html", {'templates': api.template_list("*")})

@wrap_rpc
def add(api, request):
	if request.REQUEST.has_key("name"):
		name=request.REQUEST["name"]
		type=request.REQUEST["type"]
		url=request.REQUEST["url"]
		task = api.template_add(name, type, url)
		return render_to_response("admin/template_index.html", {'templates': api.template_list("*"), "task": task})
	else:
		return render_to_response("admin/template_add.html")

@wrap_rpc
def remove(api, request, name):
	api.template_remove(name)
	return index(request)

@wrap_rpc
def set_default(api, request, type, name):
	api.template_set_default(type, name)
	return index(request)