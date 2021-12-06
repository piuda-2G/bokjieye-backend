from django.db import models


# 복지로 엔티티
class Bokjiro(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    classification = models.CharField(max_length=15, default="", blank=True, null=False)
    title = models.CharField(max_length=200, default="", blank=True, null=False)
    contents = models.TextField(default="", blank=True, null=False)
    interest = models.CharField(max_length=100, default="", blank=True, null=False)
    family = models.CharField(max_length=100, default="", blank=True, null=False)
    lifecycle = models.CharField(max_length=50, default="", blank=True, null=False)
    age = models.CharField(max_length=20, default="", blank=True, null=False)
    address = models.CharField(max_length=100, default="", blank=True, null=False)
    phone = models.CharField(max_length=30, default="", blank=True, null=False)
    department = models.CharField(max_length=50, default="", blank=True, null=False)
    db_inserted_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "bokjiro"


# 보건복지부 FAQ 엔티티
class Mohw(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    category = models.CharField(max_length=20, default="", blank=True, null=False)
    title = models.CharField(max_length=100, default="", blank=True, null=False)
    contents = models.TextField(default="", blank=True, null=False)
    createdDate = models.CharField(max_length=15, default="", blank=True, null=False)
    db_inserted_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "mohw"


# 복지혜택
class Benefit(models.Model):
    id = models.AutoField(primary_key=True)
    field = models.CharField(max_length=30, null=False, blank=True, default="")
    title = models.CharField(max_length=100, null=False, blank=True, default="")
    contents = models.TextField(null=False, blank=True, default="")
    who = models.TextField(null=False, blank=True, default="")
    howTo = models.TextField(null=False, blank=True, default="")

    class Meta:
        db_table = "benefit"
