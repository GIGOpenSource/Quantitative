from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
def auth(request):
    if request.method == 'POST':
        return JsonResponse({'status': False, 'message': "success"})
    elif request.method == 'GET':
        return JsonResponse({'status': True, 'message': "success"})
    return JsonResponse({'status':'ok','message':"success"})