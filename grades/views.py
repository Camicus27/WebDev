from django.shortcuts import render
from . import models

def assignments(request):
    return render(request, "assignments.html")

def index(request, assignment_id):
    return render(request, "index.html")

def submissions(request, assignment_id):
    return render(request, "submissions.html")

def profile(request):
    return render(request, "profile.html")

def login_form(request):
    return render(request, "login.html")
