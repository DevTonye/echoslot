from django.shortcuts import render

# landing page view
def index(request):
    return render(request, 'echoslot/index.html')