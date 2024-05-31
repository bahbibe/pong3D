from django.shortcuts import render


def chat(request):
    return render(request, 'chat/index.html')

def ChatLoginForm(request):
    return render(request, 'chat/login.html')