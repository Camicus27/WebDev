from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect
from django.db.models import Count
from . import models
from django.http import Http404, HttpResponse
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

# Helpers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def is_student(user):
    return user.groups.filter(name="Students").exists()

def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()

def is_admin(user):
    return user.is_superuser

def is_auth(user):
    return user.is_superuser or user.groups.filter(name="Teaching Assistants").exists()

def pick_grader(assgn):
    # Get TA group
    tas = models.Group.objects.get(name="Teaching Assistants")
    # Get all TA users with a total_assigned var
    ta_users = tas.user_set.all().annotate(total_assigned=Count('graded_set', filter=assgn)) # type: ignore
    
    # TA with fewest assigned
    return ta_users.order_by('total_assigned').first()

def is_past_due(assgn):
    return assgn.deadline < datetime.now(timezone.get_default_timezone())

# Page Renderers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@login_required
def assignments(request):
    assgns = models.Assignment.objects.all()
    return render(request, "assignments.html", {'assignments': assgns})

@login_required
def index(request, assignment_id):
    try:
        assgn = models.Assignment.objects.get(pk=assignment_id)
        args = {'assignment': assgn,
                'is_ta': False,
                'is_student': False}
        
        if is_student(request.user):
            args['is_student'] = True
            submission = None
            try:
                submission = models.Submission.objects.get(author=request.user, assignment_id=assignment_id)
            except models.Submission.DoesNotExist:
                pass
            
            # Is submitted
            if submission is not None:
                args['submission_url'] = submission.file.url  # <a href="{{submission_url}}" title="View submission">Submission</a>
                if is_past_due(assgn):
                    # Not yet graded
                    if submission.score is None:
                        args['submission_status'] = ('Your submission,&nbsp;<a href="' + submission.file.url + '" title="View submission">' + 
                                                     submission.file.name + '</a>,&nbsp;is being graded')
                    # Graded
                    else:
                        assgn_score = (float(submission.score) / float(assgn.points)) * float(assgn.weight)
                        assgn_perc = assgn_score / float(assgn.weight)
                        args['submission_status'] = ('Your submission,&nbsp;<a href="' + submission.file.url + '" title="View submission">' + 
                                                    submission.file.name + '</a>,&nbsp;received ' +
                                                    str(round(assgn_score, 1)) + '/' +
                                                    str(round(float(assgn.weight))) + 
                                                    ' points (' +
                                                    "{:.1%}".format(assgn_perc) + ')')
                # Not yet due
                else:
                    args['submission_status'] = ('Your current submission is&nbsp;<a href="' + submission.file.url + '" title="View submission">' + 
                                                submission.file.name + '</a>')
            # Not submitted
            else:
                if is_past_due(assgn):
                    args['submission_status'] = "You did not submit this assignment and received 0 points"
                # Not yet due
                else:
                    args['submission_status'] = "No current submission"
        elif is_ta(request.user) or is_admin(request.user):
            args['is_ta'] = True
            args['students'] = models.Group.objects.get(name="Students").user_set.count() # type: ignore
            args['submissions_assigned'] = models.Submission.objects.filter(grader=request.user, assignment_id=assignment_id).count()
        else:
            return HttpResponseForbidden("Unauthorized")
        
        return render(request, "index.html", args)
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist.")

@user_passes_test(is_student)
@login_required
def submit(request, assignment_id):
    # Get assignment
    assn = None
    try:
        assn = models.Assignment.objects.get(pk=assignment_id)
    except models.Assignment.DoesNotExist:
        pass
    
    # Get user submitted file
    try:
        submit_file = request.FILES['student_submission']
    except:
        return redirect(f'/{assignment_id}')
    
    # Get or create a user's submission and assign the file to it
    submission = None
    try:
        submission = models.Submission.objects.get(author__username=request.user.username, assignment_id=assignment_id)
        submission.file = submit_file
    except models.Submission.DoesNotExist:
        submission = models.Submission.objects.create(assignment = assn, author = request.user, grader = pick_grader(assn), file = submit_file, score = None)
    submission.save()
    
    return redirect(f'/{assignment_id}')

@user_passes_test(is_auth)
@login_required
def submissions(request, assignment_id):
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

@login_required
def show_upload(request, filename):
    # Get submission
    submiss = None
    try:
        submiss = models.Submission.objects.get(file=filename)
    except:
        raise Http404("File does not exist.")
    
    # Deny access for unauthorized users
    if request.user != submiss.grader and request.user != submiss.author and not is_admin(request.user):
        raise PermissionDenied
        
    # Send the file to be downloaded by the user
    try:
        with submiss.file.open() as fd:
            response = HttpResponse(fd)
            response["Content-Disposition"] = \
                f'attachment; filename="{submiss.file.name}"'
            return response
    except:
        raise Http404("Error downloading file.")

@login_required
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
                submissions_assigned_count = models.Submission.objects.filter(grader__username=request.user.username, assignment_id=assgn.pk).count()
                submissions.append(submissions_assigned_count)
                if submissions_assigned_count == 0:
                    if is_past_due(assgn):
                        graded.append("No submissions")
                    else:
                        graded.append("Not Due")
                else:
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
                if is_past_due(assgn):
                    # There is a submission
                    if submiss is not None:
                        # It is graded
                        if submiss.score is not None:
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

@user_passes_test(is_auth)
@login_required
def grade(request, assignment_id):
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

def login_form(request):
    args = {}
    
    if request.method == 'GET':
        args['next_path'] = request.GET.get('next', '/profile/')
    
    if request.method == 'POST':
        args['next_path'] = request.POST.get('next', '/profile/')
        
        authorizedUser = authenticate(username=request.POST.get('UsernameField', ''),
                                      password=request.POST.get('PasswordField', ''))
        if (authorizedUser is not None):
            login(request, authorizedUser)
            return redirect(args['next_path'])
        else:
            args['error_msg'] = 'Username and password do not match'
    
    return render(request, "login.html", args)

def logout_form(request):
    logout(request)
    return redirect('/profile/login/')
