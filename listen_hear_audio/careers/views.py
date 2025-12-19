from django.views.generic import DetailView, ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import JobPosting, CareersPageConfig
from .forms import JobApplicationForm


class CareersListView(ListView):
    model = JobPosting
    template_name = "careers/careers_list.html"
    context_object_name = "jobs"
    paginate_by = 20

    def get_queryset(self):
        return JobPosting.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = CareersPageConfig.get_config()
        return context


class JobDetailView(DetailView):
    model = JobPosting
    template_name = "careers/job_detail.html"
    context_object_name = "job"

    def get_queryset(self):
        return JobPosting.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = JobApplicationForm()
        return context


def apply_for_job(request, slug):
    """Handle job application form submission"""
    job = get_object_or_404(JobPosting, slug=slug, active=True)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job_posting = job
            application.save()

            messages.success(
                request,
                f'Your application for {job.title} has been submitted successfully! We will review your application and be in touch soon.'
            )
            return redirect('careers:job_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobApplicationForm()

    return render(request, 'careers/job_detail.html', {
        'job': job,
        'form': form
    })
