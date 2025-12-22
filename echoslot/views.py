from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'echoslot/index.html')

def about(request):
    return render(request, 'echoslot/about.html')

def contact(request):
    return render(request, 'echoslot/contact.html')
def api_documentation(request):
    return render(request, 'echoslot/api_documentation.html')