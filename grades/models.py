from django.db import models
from django.contrib.auth.models import User, Group

# Create your models here.
class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    weight = models.IntegerField()
    points = models.IntegerField(default=100)

    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    grader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='graded_set', null=False)
    file = models.FileField(null=False)
    score = models.FloatField(null=True)

    def __str__(self):
        return f"Submission for {self.assignment.title} by {self.author.get_full_name()}"