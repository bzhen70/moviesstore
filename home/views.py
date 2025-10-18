from django.shortcuts import render
from django.http import JsonResponse
from cart.models import MovieLocationTrend

# Create your views here.
def index(request):
    template_data = {}
    template_data['title'] = 'Movies Store'
    return render(request, 'home/index.html', {
        'template_data' : template_data})
def about(request):
    template_data = {}
    template_data['title'] = 'About'
    return render(request, 'home/about.html',
                    {'template_data': template_data})
    
def map(request):
    template_data = {'title': 'Local Popularity Map'}
    return render(request, 'home/map.html', {'template_data': template_data})

def trending_movies_api(request):
    queryset = MovieLocationTrend.objects.all()
    data = []
    for trend in queryset:
        data.append({
            'movie': trend.movie.name,
            'purchase_count': trend.purchase_count,
            'location': {
                'city': getattr(trend, 'city', ''),
                'state': getattr(trend, 'state', ''),
                'country': getattr(trend, 'country', ''),
                'lat': getattr(trend, 'latitude', 0),
                'lng': getattr(trend, 'longitude', 0),
            }
        })
    return JsonResponse({'results': data})