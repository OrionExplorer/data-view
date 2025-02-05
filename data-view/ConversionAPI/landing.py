from django.shortcuts import render


def show(request):
    return render(request, 'dataview_landing_page.html')
