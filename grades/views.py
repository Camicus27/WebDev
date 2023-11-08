from django.shortcuts import render, redirect
from . import models
from django.http import Http404

def assignments(request):
    assgns = models.Assignment.objects.all()
    return render(request, "assignments.html", {'assignments': assgns})

def index(request, assignment_id):
    try:
        student_count = models.Group.objects.get(name="Students").user_set.count()
        assgn = models.Assignment.objects.get(pk=assignment_id)
        your_submissions = models.Submission.objects.filter(grader__username="ta1", assignment_id=assignment_id).count()
        return render(request, "index.html", {'students': student_count, 'submissions_assigned': your_submissions, 'assignment': assgn})
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

def submissions(request, assignment_id):
    try:
        assgn = models.Assignment.objects.get(pk=assignment_id)
        your_submissions = models.Submission.objects.filter(grader__username="ta1", assignment_id=assignment_id).order_by('author__username')
        return render(request, "submissions.html", {'submissions_assigned': your_submissions, 'assignment': assgn})
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

def profile(request):
    try:
        assgns = models.Assignment.objects.all()
        submissions = models.Submission.objects.filter(grader__username="ta1").count()
        graded = models.Submission.objects.filter(grader__username="ta1", score__isnull=False).count()
        return render(request, "profile.html", {'graded': graded, 'submissions_assigned': submissions, 'assignments': assgns})
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

def login_form(request):
    return render(request, "login.html")

def grade(request, assignment_id):
    for key in request.POST:
        if key.startswith('grade-'):
            try:
                submission_id = int(key.split('-')[1])
                submission = models.Submission.objects.get(pk=submission_id)
                submission.score = float(request.POST[key])
                submission.save()
            except ValueError:
                continue

    return redirect(f'/{assignment_id}/submissions')