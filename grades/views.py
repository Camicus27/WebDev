from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect
from . import models
from django.http import Http404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout

# Helpers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def is_student(user):
    return user.groups.filter(name="Students").exists()

def is_ta(user):
    return user.is_authenticated and user.groups.filter(name="Teaching Assistants").exists()

def is_admin(user):
    return user.is_authenticated and user.is_superuser

# Page Renderers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def assignments(request):
    assgns = models.Assignment.objects.all()
    return render(request, "assignments.html", {'assignments': assgns})

def index(request, assignment_id):
    try:
        args = {'assignment': models.Assignment.objects.get(pk=assignment_id),
                'is_ta': False,
                'is_student': False}
        
        if is_student(request.user):
            args['is_student'] = True
        elif is_ta(request.user):
            args['is_ta'] = True
            args['students'] = models.Group.objects.get(name="Students").user_set.count() # type: ignore
            args['submissions_assigned'] = models.Submission.objects.filter(grader__username=request.user.username, assignment_id=assignment_id).count()
        else:
            return HttpResponseForbidden("Unauthorized")
        
        return render(request, "index.html", args)
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

def submissions(request, assignment_id):
    if is_student(request.user):
        return HttpResponseForbidden("Unauthorized")
    
    try:
        submiss = 0
        if is_admin(request.user):
            submiss = models.Submission.objects.filter(assignment_id=assignment_id).order_by('author__username')
        else:
            submiss = models.Submission.objects.filter(grader__username=request.user.username, assignment_id=assignment_id).order_by('author__username')
        
        return render(request, "submissions.html", {'assignment': models.Assignment.objects.get(pk=assignment_id),
                                                    'submissions_assigned': submiss})
    
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

def profile(request):
    try:
        assgns = models.Assignment.objects.all()
        graded = []
        args = {'usrname': request.user,
                'is_student': False,
                'assignments': assgns}
        
        if is_admin(request.user):
            submissions = []
            for assgn in assgns:
                submissions.append(models.Submission.objects.filter(assignment_id=assgn.pk).count())
                graded.append(models.Submission.objects.filter(assignment_id=assgn.pk, score__isnull=False).count())
            args['submissions_assigned'] = submissions
        elif is_ta(request.user):
            submissions = []
            for assgn in assgns:
                submissions.append(models.Submission.objects.filter(grader__username=request.user.username, assignment_id=assgn.pk).count())
                graded.append(models.Submission.objects.filter(grader__username=request.user.username, assignment_id=assgn.pk, score__isnull=False).count())
            args['submissions_assigned'] = submissions
        else:
            # earned points = (score / totalPoints) * weight
            # total class points = all earned points / all weights(graded and missing)
            args['is_student'] = True
            earned_points = 0
            total_points = 0
            for assgn in assgns:
                
                submiss = None
                try:
                    submiss = models.Submission.objects.get(author__username=request.user.username, assignment_id=assgn.pk)
                except models.Submission.DoesNotExist:
                    pass
                
                # Assgn is due
                if assgn.deadline < datetime.now(timezone.get_default_timezone()):
                    # There is a submission
                    if submiss:
                        # It is graded
                        if submiss.score:
                            total_points += assgn.weight
                            assgn_score = (float(submiss.score) / float(assgn.points)) * float(assgn.weight)
                            earned_points += assgn_score
                            assgn_perc = assgn_score / float(assgn.weight)
                            graded.append("{:.1%}".format(assgn_perc))
                        # Not graded
                        else:
                            graded.append("Ungraded")
                    # No submission
                    else:
                        total_points += assgn.weight
                        graded.append("Missing")
                else:
                    graded.append("Not Due")
            
            args['final_grade'] = "{:.1%}".format(earned_points / float(total_points))
            
        args['graded'] = graded
        return render(request, "profile.html", args)
    
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

def login_form(request):
    if request.method == 'POST':
        authorizedUser = authenticate(username=request.POST.get('UsernameField', ''),
                                      password=request.POST.get('PasswordField', ''))
        
        if (authorizedUser is not None):
            login(request, authorizedUser)
            return redirect('/profile')
    
    return render(request, "login.html")

def logout_form(request):
    logout(request)
    return redirect('/profile/login/')

def grade(request, assignment_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Unauthorized")
    
    for key in request.POST:
        if key.startswith('grade-'):
            submission_id = int(key.split('-')[1])
            submission = models.Submission.objects.get(pk=submission_id)
            try:
                submission.score = float(request.POST[key])
                submission.save()
            except ValueError:
                submission.score = None
                submission.save()

    return redirect(f'/{assignment_id}/submissions')

