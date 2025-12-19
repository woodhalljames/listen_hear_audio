from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class CareersPageConfig(models.Model):
    """Configuration for the careers page"""
    introduction = models.TextField(
        blank=True,
        help_text="Introduction text displayed at the top of the careers page"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Careers Page Configuration"
        verbose_name_plural = "Careers Page Configuration"

    def __str__(self):
        return f"Careers Page Config (updated: {self.updated_at.strftime('%Y-%m-%d')})"

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class JobPosting(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Job Posting"
        verbose_name_plural = "Job Postings"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("careers:job_detail", kwargs={"slug": self.slug})


class JobApplication(models.Model):
    """Job application submitted by candidates"""
    job_posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    cover_letter = models.TextField(blank=True, help_text="Optional cover letter")
    resume = models.FileField(
        upload_to='careers/resumes/',
        help_text="Upload your resume (PDF format recommended)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"

    def __str__(self):
        return f"{self.name} - {self.job_posting.title}"
